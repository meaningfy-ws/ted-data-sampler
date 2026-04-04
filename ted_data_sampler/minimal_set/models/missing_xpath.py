from typing import Optional

from pydantic import BaseModel


class MissingXPathEntry(BaseModel):
    """
    Represents a missing/uncovered XPath entry from the Mapping Workbench.

    Attributes:
        sdk_element_id: The BT (Business Term) or ND (Node) identifier.
            Example: "BT-27-Procedure" or "ND-ProcurementProjectLot"
        type: Either "FIELD" or "NODE" indicating the type of element.
        absolute_xpath: Full XPath from root to the element, including any
            SDK predicates (e.g., [cbc:ID/@schemeName='LotsGroup']).
        xpath_condition: Optional additional condition expressed as XPath/XQuery
            that must be satisfied. Evaluated at the iterator context node.
            Example: "not(exists(efac:FieldsPrivacy[...]) and efbc:ParameterCode/text() = 'unpublished')"
        abs_xpath_reduced: Simplified XPath without predicates, used for fast
            text-based candidate discovery. Segments separated by '/'.
            Example: "cac:ProcurementProjectLot/cac:TenderingTerms/cac:AwardingTerms/cac:AwardingCriterion/cbc:Description"
        iterator_xpath: The parent/iterator node XPath used as context when
            evaluating xpath_condition. For FIELD types, this is the parent node;
            for NODE types, this is the node itself (same as absolute_xpath).
            Example: "/*/cac:ProcurementProjectLot[cbc:ID/@schemeName='LotsGroup']/cac:TenderingTerms/cac:AwardingTerms/cac:AwardingCriterion"
    """
    sdk_element_id: str
    type: str
    absolute_xpath: str
    xpath_condition: Optional[str] = None
    abs_xpath_reduced: str
    iterator_xpath: str
