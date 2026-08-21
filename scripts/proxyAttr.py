import maya.cmds as cmds
def addProxyAttribute(node, existingNode, existingAttr, proxyAttr="", channelBox=True, nonKeyable=False):
    """Creates a new proxy attribute on the given node.

    If `proxyAttr` is left empty the function will use the `existingAttr` name as the `proxyAttr` name.

    :param node: The maya object/node that the proxy attribute will be created on
    :type node: str
    :param existingNode: The Maya obj that already exists with the attribute to be copied
    :type existingNode: str
    :param existingAttr: The existing attribute to be copied on the existing obj, don't include obj
    :type existingAttr: str
    :param proxyAttr: the name of the proxy attribute, if empty will clone the existingAttr name
    :type proxyAttr: str
    :param channelBox: is the proxy attribute visible in the channelBox?
    :type channelBox: bool
    :param nonKeyable: is the proxy attribute keyable if in the channelBox?
    :type nonKeyable: bool

    :return node: The object name with the new proxy attribute
    :rtype obj: str
    :return proxyAttr: The attribute of the new proxy attribute
    :rtype proxyAttr: str
    """
    if not proxyAttr:
        proxyAttr = existingAttr
    # get attribute type, not sure if this is needed
    attrType = cmds.attributeQuery(existingAttr, node=existingNode, attributeType=True)
    cmds.addAttr(node, longName=proxyAttr, proxy=".".join([existingNode, existingAttr]), keyable=channelBox,
                 attributeType=attrType)

    # If parent attribute then the child attrs won't show in channel box so set all children as keyable
    childAttrs = cmds.attributeQuery(proxyAttr, node=node, listChildren=True)
    if childAttrs:
        for attr in childAttrs:
            cmds.setAttr(".".join([node, attr]), keyable=True)
            # Attribute children have the original name in the child name, so remove it so it's not doubled
            # "xxxvector1Y" becomes 'xxxY' or "vector1vector1Y" becomes "vector1Y"
            newName = attr.replace(existingAttr, "", 1)
            cmds.renameAttr(".".join([node, attr]), newName)

    # Set channel box and non-keyable -------------------------------
    if not channelBox:  # Hiding the attribute so leave keyable as False which is the default
        cmds.setAttr(".".join([node, proxyAttr]), channelBox=channelBox)
        return node, proxyAttr
    cmds.setAttr(".".join([node, proxyAttr]), channelBox=True)  # Must be True
    cmds.setAttr(".".join([node, proxyAttr]), keyable=not nonKeyable)

    return node, proxyAttr

driver_list = cmds.ls(sl=True)
driver_attr_list = ['scaleMult','scaleMin','scaleMax']
driven_list = cmds.ls(sl=True)
for driver, driven in zip(driver_list, driven_list):
    for driver_attr in driver_attr_list:
        addProxyAttribute(driven, driver, driver_attr, proxyAttr='', channelBox=True, nonKeyable=False)