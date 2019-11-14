from typing import *
import mysql.connector
import prompt_toolkit
import datetime
import traceback

def main():
    cursor = connection.cursor()

    cursor.execute("select * from student")
    values = cursor.fetchall()
    cursor.close()
    print(values)

    profile = {}

    # login view
    while True:
        # username = prompt_toolkit.shortcuts.input_dialog(
        #     title="NU Login",
        #     text="Username",
        #     cancel_text="Quit"
        # )
        # if username == None:
        #     exit()

        # password = prompt_toolkit.shortcuts.input_dialog(
        #     title="NU Login",
        #     text="Password",
        #     password=True
        # )
        # if password == None:
        #     continue
        username = "Linda Smith"
        password = "lunch"

        cursor = connection.cursor()
        cursor.execute("select id, name, password from student where student.name = %s and student.password = %s", (username, password))
        values = cursor.fetchall()
        cursor.close()
        if len(values) == 0:
            prompt_toolkit.shortcuts.message_dialog(
                title = "NU Login",
                text = "Wrong username or password",
                style = prompt_toolkit.styles.Style.from_dict({
                    "dialog": "bg:#ff0000",
                }),
            )
            continue
        else:
            profile["id"] = values[0][0]
            profile["username"] = values[0][1]
            profile["password"] = values[0][2]
            print(profile)
            break

if __name__ == "__main__":
    try:
        connection = mysql.connector.connect(user="root", password="19961226syc", database="project3-nudb", host="localhost", port=3306)
        main()
    except:
        traceback.print_exc()
        connection.close()