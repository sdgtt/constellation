from app.models.boot_tests import BootTest
from app.models.data_types import BoardStatus
from app.models.db import DB


class Board(BootTest):
    def __init__(self, board_name, latest_boot_test=None):
        BootTest.__init__(self, latest_boot_test)
        self.board_name = board_name
        self.latest_boot_test = latest_boot_test
        self._status = self.__get_status()
        self.is_online = self.__is_online()  # True/False

    def __get_status(self):
        if hasattr(self, "uboot_reached"):
            self._status = BoardStatus.UBOOT_READY
            if hasattr(self, "linux_prompt_reached"):
                self._status = BoardStatus.LINUX_READY
        else:
            self._status = BoardStatus.POWER_ON
        return BoardStatus.DEACTIVATED

    def __is_online(self):
        if hasattr(self, "linux_prompt_reached"):
            return self.linux_prompt_reached
        return None

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status):
        if isinstance(new_status, BoardStatus):
            self._status = new_status
        else:
            raise ValueError(
                "{} must be of type data_types.BoardStatus".format(new_status)
            )

    def display(self):
        return self.__dict__


class Boards:
    def __init__(
        self, jenkins_project_name=None, source_adjacency_matrix=None, deprecated=[]
    ):
        self._boards = []
        self.db = DB()
        # get list of boards
        boards = self.db.search(
            agg_field="boot_folder_name",
            jenkins_project_name=jenkins_project_name,
            source_adjacency_matrix=source_adjacency_matrix,
        )["aggregates"]
        # create boards object from latest boot of that board
        for board in boards:
            latest_board_boot_result = self.db.search(
                size=1,
                jenkins_project_name=jenkins_project_name,
                source_adjacency_matrix=source_adjacency_matrix,
                boot_folder_name=board,
            )
            if board not in deprecated:
                self._boards.append(Board(board, latest_board_boot_result["hits"][0]))

    @property
    def boards(self):
        return self._boards

    @property
    def boards_name_list(self):
        return [b.board_name for b in self._boards]


if __name__ == "__main__":
    # b = Board("test")
    # print(b.__dict__)
    # b.status = "invalid"
    # assert b.status == BoardStatus.LINUX_READY
    B = Boards()
    print([b.display() for b in B.boards])
    print(B.boards_name_list)
