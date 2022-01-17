# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the License);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Main module for DBO explorer."""
import ast
import colorama
from termcolor import colored
from typing import List

from lib import model
from lib.model import StandardField

DEFAULT_MATCHED_TYPES_LIST_SIZE = 10
colorama.init()

def _InputFieldsFromUser(ontology, manual: bool = False) -> List[StandardField]:
  """Method to take in field inputs from the user.

  Args:
    ontology: Instance of OntologyWrapper class.
    manual: boolean where users will input field names one by one if True.

  Returns:
    A list of StandardField objects corresponding to the input field names.

  """
  standard_field_list = []
  if manual:
    raw_field_list = []
    field_number = input('Number of entity fields: ')
    for i in range(1, int(field_number) + 1):
      field_name = input(f'Field name #{i}: ')
      raw_field_list.append(field_name)
  else:
    raw_fields = input('Paste your fields here: ')
    raw_field_list = raw_fields.replace(' ', '').split(',')
  for field in raw_field_list:
    standard_field = StandardField(
        standard_field_name=field,
        namespace_name=''
    )
    if ontology.IsFieldValid(standard_field):
      standard_field_list.append(standard_field)
  return standard_field_list

def GetFieldsForTypeName(ontology):
  """Prints a list of corresponding fields for an ontology entity type.

  Args:
    ontology: An instance of the OntologyWrapper class.
  """
  namespace = input('Enter a namespace: ').upper()
  type_name = input(f'Enter a type name defined in {namespace}: ').upper()
  fields = ontology.GetFieldsForTypeName(namespace, type_name)
  print(f'\nFields for {namespace}/{type_name}:')
  for field in fields:
    print(colored(field, 'green'))

def GetTypesForFieldList(ontology):
  """Prints a list of entity types matching a list of input fields.

  Args:
    ontology: An instance of the OntologyWrapper class.
  """
  print('1. Input fields one by one\n2. Paste comma-separated list of fields')
  input_decision = input('Input type: ')
  manual_input = False
  if ast.literal_eval(input_decision) == 1:
    manual_input = True
  standard_field_list = _InputFieldsFromUser(ontology, manual_input)

  entity_type_match_dict = {}
  for i, match in enumerate(ontology.GetEntityTypesFromFields(
      standard_field_list)):
    entity_type_match_dict[i] = match
  for i in range(DEFAULT_MATCHED_TYPES_LIST_SIZE):
    print(colored(f'{i+1}. {entity_type_match_dict[i]}', 'green'))
  match_selection = input('Would you like to see all matches?(y/n):\n')
  if match_selection == 'y':
    for i, match in entity_type_match_dict.items():
      print(f'{i+1}. {match}')
  print('Would you like to see field comparisons for any of these matches?')
  visualize = input('(y/n): ')
  if visualize == 'y':
    visualize_done = False
    while not visualize_done:
      comparison_number = ast.literal_eval(input(
          'which match would you like to visualize?\nmatch number: '))
      print_match = entity_type_match_dict[comparison_number - 1]
      print(ontology.PrintFieldSetComparison(print_match))
      repeat_comparison = input(
          'Would you like to see another match comparison?\n(y/n): ')
      if repeat_comparison == 'n':
        break
      elif repeat_comparison == 'y':
        continue
      else:
        raise ValueError('Please enter proper value for decision tree')

def ValidateFieldName(ontology):
  """Prints whether a fully qualified field is valid in the DB ontology.

  Args:
    ontology: An instance of the OntologyWrapper class
  """
  namespace = input('Enter a namespace(leave blank for global): ').upper()
  field_name = input('Enter a field name to validate: ')
  standard_field = model.StandardField(namespace, field_name)
  field_is_valid = ontology.IsFieldValid(standard_field)
  if namespace == '':
    namespace = 'global namespace'
  if field_is_valid:
    print(colored(
        f'{field_name} is defined in {namespace}: {field_is_valid}', 'green'))
  else:
    print(colored(
        f'{field_name} is defined in {namespace}: {field_is_valid}', 'red'))
