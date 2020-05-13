import sqlite3
import unittest
from HiCity import HiCity


class TestImportDB(unittest.TestCase):
    def setUp(self):
        print("The part of the database import test begins:")
        self.city = {'天津': '101030100', '江津': '101040500'}
        self.DB_name = 'test/City'

    def test_importDB(self):
        HiCity.importDB(self.city, self.DB_name)

    def tearDown(self):
        print("End of importDB test!")


class TestCarryoutSQL(unittest.TestCase):
    def setUp(self):
        print("Database addition, deletion, modification and inspection test:")
        self.DB_name = "test/City.db"

    def test_carryoutsql_insert(self):
        SQL1 = "INSERT INTO City VALUES (3, '北京', '101010102');"
        SQL2 = "INSERT INTO City VALUES (4, '海淀', '101010200');"
        result1 = HiCity.carryOutSQL(SQL1, self.DB_name)
        self.assertTrue(isinstance(result1, list))
        result2 = HiCity.carryOutSQL(SQL2, self.DB_name)
        self.assertTrue(isinstance(result2, list))

    def test_carryoutsql_delete(self):
        SQL = "DELETE FROM City WHERE CityName = '海淀';"
        result = HiCity.carryOutSQL(SQL, self.DB_name)
        self.assertTrue(isinstance(result, list))

    def test_carryoutsql_update(self):
        SQL = "UPDATE City SET Code = '101010100' WHERE CityName = '北京';"
        result = HiCity.carryOutSQL(SQL, self.DB_name)
        self.assertTrue(isinstance(result, list))

    def test_carryoutsql_select(self):
        SQL = "SELECT * FROM City WHERE CityName = '北京';"
        result = HiCity.carryOutSQL(SQL, self.DB_name)
        self.assertEqual(result[0][2], "101010100")

    def tearDown(self):
        print("End of database test!")


class TestBackupExecl(unittest.TestCase):
    def setUp(self):
        print("Backup to execl part test starts:")
        self.city = {'北京': '101010100', '海淀': '101010200'}

    def test_backup_execl(self):
        HiCity.backup_execl(self.city)

    def tearDown(self):
        print("Backup to execl part test is over!")


class TestFuzzyMatching(unittest.TestCase):
    def setUp(self):
        print("Start of fuzzy search test:")
        self.city = {'北京': '', '北辰': '', '朝阳': '', '沈阳': ''}
        self.word = "北"

    def test_fuzzy_matching(self):
        matchResult = HiCity.fuzzy_matching(self.word, self.city)
        self.assertEqual(len(matchResult), 2)

    def tearDown(self):
        print("End of fuzzy search test!")


class TestLogRecord(unittest.TestCase):
    def setUp(self):
        print("Logging module test begins:")
        self.info = "This is a test case!"

    def test_log_record(self):
        HiCity.log_record(self.info)

    def tearDown(self):
        print("End of log module test!")


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestImportDB("test_importDB"))
    suite.addTest(TestCarryoutSQL("test_carryoutsql_insert"))
    suite.addTest(TestCarryoutSQL("test_carryoutsql_delete"))
    suite.addTest(TestCarryoutSQL("test_carryoutsql_update"))
    suite.addTest(TestCarryoutSQL("test_carryoutsql_select"))
    suite.addTest(TestBackupExecl("test_backup_execl"))
    suite.addTest(TestFuzzyMatching("test_fuzzy_matching"))
    suite.addTest(TestLogRecord("test_log_record"))

    runner = unittest.TextTestRunner()
    runner.run(suite)
