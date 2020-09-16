import logging

log = logging.getLogger(__name__)


class SportService:

    def __init__(self, config):
        self.sports = config.sports if config is not None else []

    def getSportFor(self, inStr):
        log.debug(f"Getting sport for {inStr}")

        if inStr is None:
            return None

        sportMatches = {}
        bestMatch = None
        bestScore = 0

        for sport in self.sports:
            (match, score) = sport.matchFor(inStr)
            sportMatches[sport.name] = (match, score)
            if score > bestScore:
                bestScore = score
                bestMatch = sport

        if bestMatch is None:
            log.debug(f"No sport matches for {inStr}")
        else:
            log.debug(sportMatches)
            log.debug(f"Best is {bestMatch.name} ({bestScore})")

        return bestMatch if bestScore > 60 else None
