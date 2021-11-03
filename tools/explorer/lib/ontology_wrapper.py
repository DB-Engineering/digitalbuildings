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

"""Ontology wrapper class for DBO explorer."""
from typing import List, Set

from lib.model import EntityTypeField
from lib.model import Match
from lib.model import StandardField
from lib import model

from yamlformat.validator.entity_type_lib import EntityType
from yamlformat.validator.entity_type_manager import EntityTypeManager
from yamlformat.validator.presubmit_validate_types_lib import ConfigUniverse

class OntologyWrapper(object):
  """Class providing an interface to do lookups on DBO.

     Attributes:
       universe: A ConfigUniverse object detailing the various universes in
         DBO.
       manager: An EntityTypeManager object to find greatest common subsets
         of fields between entity types and complete lists of inherited
         fields for a concrete entity. This is primarily used for
         _CreateMatch().
       match_score_threshold: When best git matches are desired, this
         threshold is used to filter matches that have a considerably low match
         score

    Returns:
      An instance of OntologyWrapper class.
  """

  def __init__(self, universe: ConfigUniverse):
    """Init.

    Args:
      universe: an instantiated ConfigUniverse Object with inherited fields
        expanded.
    """
    super().__init__()
    self.universe = universe
    self.manager = EntityTypeManager(self.universe)
    self.match_score_threshold = -0.5

  def GetFieldsForTypeName(
      self,
      namespace: str,
      entity_type_name: str,
      required_only: bool = False) -> List[EntityTypeField]:
    """Gets a list of fields for a given typename within a namespace.

    Args:
      namespace: the name of the namespace as a string.
      entity_type_name: the name of the entity type as a string.
      required_only: when true will return only required fields for a given
        type.

    Returns:
      result_fields: a list of EntityTypeField objects.

    Raises:
      Exception: when inherited fields are not expanded.
    """
    entity_type = self.universe.entity_type_universe.GetEntityType(
        namespace, entity_type_name)
    if entity_type is None:
      if not namespace:
        raise ValueError(
            f'\n{entity_type_name} is not defined in global namespace.')
      else:
        raise ValueError(
            f'\n{entity_type_name} is not defined in namespace: {namespace}.')
    if not entity_type.inherited_fields_expanded:
      raise Exception(
          'Inherited fields must be expanded to query fields.\n' +
          'Run NamespaceValidator on your ConfigUniverse to expand fields.')
    # Entity_type_lib.FieldParts NamedTuple to EntityTypeField object.
    entity_type_fields = []
    for qualified_field in entity_type.GetAllFields().values():
      new_entity_type_field = EntityTypeField(qualified_field.field.namespace,
                                              qualified_field.field.field,
                                              qualified_field.optional,
                                              qualified_field.field.increment)
      entity_type_fields.append(new_entity_type_field)

    if required_only:
      entity_type_fields = [
          field for field in entity_type_fields if not field.IsOptional()
      ]
    entity_type_fields_sorted = sorted(
        entity_type_fields,
        key=lambda x: x.GetStandardFieldName(),
        reverse=False)

    return entity_type_fields_sorted

  def _CalculateMatchScore(self, concrete_fields: Set[StandardField],
                           canonical_fields: Set[EntityTypeField])-> float:
    """Calculates a match's score.

    The score of a match is determined by calculating the average of two
    f-scores. The first f-score is the measure of correctly matched required
    fields in the canonical type and the second f-score is the measure of
    correctly matched fields regardless of optionality. Adding the two f-scores
    creates a preference for matches with a higher quantity of matched required
    canonical fields, and dividing by 2 keeps the range of the function in
    [-1, 1].

    Args:
      concrete_fields: A set of StandardField objects belonging to the
        concrete entity being matched.
      canonical_fields: A set of EntityTypeField objects belonging to an Entity
        Type defined in DBO.

    Returns:
      A match's score as a floating point number.
    """

    required_canonical_fields = {
        model.StandardizeField(field) for field in canonical_fields
        if not field.IsOptional()
    }

    standard_canonical_fields: Set[StandardField] = set()
    for field in canonical_fields:
      standard_canonical_fields.add(model.StandardizeField(field))

    ma = len(concrete_fields.intersection(standard_canonical_fields))
    mr = len(concrete_fields.intersection(required_canonical_fields))
    tr = len(required_canonical_fields)
    c = len(concrete_fields)
    e = len(concrete_fields.difference(standard_canonical_fields))
    a = len(required_canonical_fields.difference(concrete_fields))

    if c <= 0:
      raise ValueError('Concrete field set cannot be empty.')
    if tr <= 0:
      match_score = ((ma - e) / c) / 2.0
    else:
      match_score = (((ma - e) / c) + ((mr - a) / tr)) / 2.0

    return match_score

  def _CreateMatch(self, field_list: List[StandardField],
                   entity_type: EntityType) -> Match:
    """Creates a Match instance for an EntityType object and a list of
    StandardField objects.

    calls _CalculateMatchWeight() on field_list and the set of fields belonging
    to entity_type. The scoring function outputs a float signifying the
    closeness of the match, and an instance of the Match class is created with
    field_list, entity_type, and match_score as arguments.

    Args:
      field_list: A list of EntityTypeField objects for a concrete entity.
      entity_type: An EntityType object.

    Returns:
      An instance of Match class.
    """
    canonical_field_set = set()
    for qualified_field in entity_type.GetAllFields().values():
      new_entity_type_field = EntityTypeField(
          qualified_field.field.namespace,
          qualified_field.field.field,
          qualified_field.optional,
          qualified_field.field.increment
      )
      canonical_field_set.add(new_entity_type_field)

    match_score = self._CalculateMatchScore(
        concrete_fields=frozenset(field_list),
        canonical_fields=frozenset(canonical_field_set)
    )
    new_match = Match(
        field_list,
        entity_type,
        match_score
    )
    return new_match

  def GetEntityTypesFromFields(self,
                               field_list: List[StandardField],
                               general_type: str = None,
                               best_fit: bool = False) -> List[Match]:
    """Get a list of Match objects containg information on a strength of a
    match between all entity types defined in DBO and a list of concrete
    fields.

    Args:
      field_list: A list of StandardField objects to match to an entity
      general_type: A string indicating a general type name to filter return
        results.
      best_fit: If True, then return a list of Match objects whose score is
        greater than -0.5. If False, return the entire list of Match objects.

    Returns:
      A sorted list of Match objects.
    """
    entity_type_list = []
    type_namespaces_list = self.universe.GetEntityTypeNamespaces()
    for tns in type_namespaces_list:
      for entity_type in tns.valid_types_map.values():
        if entity_type.is_abstract or entity_type.GetAllFields() == {}:
          continue
        if general_type is not None:
          if general_type.upper() in entity_type.unqualified_parent_names:
            entity_type_list.append(entity_type)
        else:
          entity_type_list.append(entity_type)

    match_list = []
    for entity_type in entity_type_list:
      match_list.append(self._CreateMatch(field_list, entity_type))

    match_list_sorted = sorted(
        match_list,
        key=lambda x: x.GetMatchScore(),
        reverse=False
    )
    if best_fit:
      return [
          match for match in match_list_sorted
          if match.GetMatchScore() > self.match_score_threshold
      ]
    return match_list_sorted

  def IsFieldValid(self, field: StandardField) -> bool:
    """A method to validate a field name against the ontology."""
    if not isinstance(field, StandardField):
      raise TypeError('Field argument must be a StandardField object.\n' +
                      f'You provided a {type(field)} object.')
    namespace_name = field.GetNamespaceName()
    standard_field_name = field.GetStandardFieldName()
    validity = self.universe.field_universe.IsFieldDefined(
        namespace_name=namespace_name, fieldname=standard_field_name)
    return validity
