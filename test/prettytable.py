import pandas as pd
from io import StringIO
from tabulate import tabulate
import unittest

def create_tmplist():
    return [['a', 'b']]

class testX(unittest.TestCase):
    def test_printtable(self):
        columns = ['model', '1st', '1. kfold', '2nd', '2. kfold', 'best score']

        df = pd.DataFrame(
            [
                ['Gradinet', '0.3', '0.4', '2.3', '4.4', '4.4'],
                ['GradinetAAAAAAAAAAAAAAAAA', '0.3', '0.4', '2.3', '4.4', '4.4'],
                ['Gradinet', '0.3', '0.4', '2.3', '4.4', '4.4'],
            ], columns=columns )
        print(tabulate(df, headers='keys', tablefmt='psql'))


        data = [['Gradinet', '0.3', '0.4', '2.3', '4.4', '4.4'], 
                ['GradinetAAAAAAAAAAAAAAAAA', '0.3', '0.4', '2.3', '4.4', '4.4'],
                ['Gradinet', '0.3', '0.4', '2.3', '4.4', '4.4']]
        print (tabulate(data, headers=columns))

    def test_list_append(self):
        r = []
        for x in range(5):
            r.extend(create_tmplist())

        print(tabulate(r, headers=['a', 'b']))


if __name__ == '__main__':
    unittest.main()