import logging

log = logging.getLogger(__name__)


class TeamSpec:
    def __init__(self, teamName, sportName=None):
        self.teamName = teamName
        self.sportName = sportName

    def __eq__(self, other):
        if isinstance(other, TeamSpec):
            return self.teamName == other.teamName \
                   and self.sportName == other.sportName

        return False

    def __str__(self):
        if self.sportName is None:
            return self.teamName
        else:
            return f"{self.teamName} ({self.sportName})"

    def __repr__(self):
        return self.__str__()
