import logging
from logging import Logger
from typing import Optional

from ted_data_sampler.core.adapters.XPathValidator import XPATHValidator
from ted_data_sampler.minimal_set.models.missing_xpath import MissingXPathEntry


def validate_entry(
    validator: XPATHValidator,
    entry: MissingXPathEntry,
    logger: Optional[Logger] = None
) -> bool:
    """
    Validate whether a notice covers a missing XPath entry using two-stage XPath checking.

    This function performs the core validation logic for the gap filler algorithm.
    It uses real XPath execution against the XML content (not string matching) to
    ensure that both structural presence AND any business conditions are satisfied.

    Stage A - Absolute XPath Check:
        Runs the absolute_xpath query against the document to find matching elements.
        The absolute_xpath may contain SDK predicates (e.g., [cbc:ID/@schemeName='LotsGroup'])
        that are part of navigation, not conditions.

    Stage B - XPath Condition Check (only if condition exists):
        If xpath_condition is present, evaluates it at each iterator context node.
        The iterator_xpath identifies the parent/iterator node that serves as context
        for evaluating the condition. For each matching iterator node:
        1. Set it as the XPath context via set_context()
        2. Evaluate the xpath_condition
        3. If condition returns true, the entry is covered

    Args:
        validator: An XPATHValidator instance with parsed XML content.
        entry: The MissingXPathEntry to validate.
        logger: Optional logger for error messages.

    Returns:
        True if the notice covers the entry (both stages pass), False otherwise.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Stage A: absolute xpath query
    result = validator.check_xpath_expression(entry.absolute_xpath)
    if result is None or result.size == 0:
        return False

    # No condition → element found, covered
    if not entry.xpath_condition:
        return True

    # Stage B: evaluate condition at each iterator context node
    iterator_result = validator.check_xpath_expression(entry.iterator_xpath)
    if iterator_result is None or iterator_result.size == 0:
        return False

    for i in range(iterator_result.size):
        try:
            item = iterator_result.item_at(i)
            context_node = item.get_node_value()
            validator.xpp.set_context(xdm_item=context_node)

            cond_result = validator.check_xpath_expression(entry.xpath_condition)
            if cond_result is not None and str(cond_result).strip().lower() == "true":
                validator.restore_document_context()
                return True
        except Exception as e:
            logger.debug(f"Condition evaluation error for {entry.sdk_element_id}: {e}")
            continue

    validator.restore_document_context()
    return False
