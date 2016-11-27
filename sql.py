from sqlalchemy import create_engine
import pandas as pd

def main():
    
    data =  [[i, i, i] for i in range(10)]
    data = pd.DataFrame(data, columns=
            ['THETA1', 'THETA2', 'THETA3'])

    con = create_engine('mysql+mysqlconnector://root:passwd@localhost:3306/ECE_439')
    data.to_sql(name='ANGLES', con=con, if_exists='replace', index_label='ID')
    print(data)


if __name__ == "__main__":
    main()
