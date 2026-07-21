from backend.repository import SupabaseRepository


class Result:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.start = 0
        self.end = 999

    def select(self, _columns):
        return self

    def eq(self, column, value):
        self.rows = [row for row in self.rows if row[column] == value]
        return self

    def in_(self, column, values):
        self.rows = [row for row in self.rows if row[column] in values]
        return self

    def order(self, column):
        self.rows = sorted(self.rows, key=lambda row: row[column])
        return self

    def range(self, start, end):
        self.start = start
        self.end = end
        return self

    def execute(self):
        return Result(self.rows[self.start : self.end + 1])


class FakeClient:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        if name == "projects":
            return FakeQuery(list(self.rows))
        if name == "rob_rub_project_mapping":
            return FakeQuery([])
        raise AssertionError(name)


def test_hierarchy_queries_paginate_beyond_supabase_default_limit():
    rows = [
        {
            "ro": f"RO-{index // 50:02d}",
            "piu": f"PIU-{index // 25:02d}",
            "project_name": f"Project {index:04d}",
            "upc": f"UPC-{index:04d}",
        }
        for index in range(1205)
    ]
    repository = SupabaseRepository(FakeClient(rows))

    assert len(repository.list_ros()) == 25
    assert "RO-24" in repository.list_ros()
    assert len(repository.list_pius("RO-20")) == 2
    assert len(repository.list_projects("RO-20", "PIU-40")) == 25
