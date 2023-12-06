# encoding: utf-8

from myLogger import logger

def createParagraphStyle(**kwargs):
    logger.debug("createParagraphStyle %s", str(kwargs))

def createCharStyle(**kwargs):
    logger.debug("createCharacterStyle %s", str(kwargs))

