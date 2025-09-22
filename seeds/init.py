import psycopg2, os

DATABASE_URL = os.getenv("DATABASE_URL","postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require")

def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    sqlfile = os.path.join(os.path.dirname(__file__),'seed.sql')
    with open(sqlfile,'r',encoding='utf-8') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()
    print("Seeds aplicados com sucesso.")

if __name__=='__main__':
    run()