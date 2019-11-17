from typing import *
import mysql.connector
import prompt_toolkit as pt
import datetime
import traceback

profile = {}
cur = []

def handler(v):
    pt.application.get_app().exit(result = v)

def getProfile(id):
    cursor = connection.cursor()
    cursor.execute("select id, name, password, address from student where student.id = %s", (id, ))
    values = cursor.fetchall()
    cursor.close()
    return {
        "id": values[0][0],
        "name": values[0][1],
        "password": values[0][2],
        "address": values[0][3],
    }

def main():
    cursor = connection.cursor()

    cursor.execute("select * from student")
    values = cursor.fetchall()
    cursor.close()
    #print(values)
    showLoginView()

# login view
def showLoginView():
    while True:
        username = pt.shortcuts.input_dialog(
            title="NU Login",
            text="Username",
            cancel_text="Quit"
        )
        if username == None:
            exit()

        password = pt.shortcuts.input_dialog(
            title="NU Login",
            text="Password",
            password=True
        )
        if password == None:
            continue
        # username = "Linda Smith"
        # password = "lunch"

        cursor = connection.cursor()
        cursor.execute("select id, name, password, address from student where student.name = %s and student.password = %s", (username, password))
        values = cursor.fetchall()
        #print(values)
        cursor.close()
        
        if len(values) == 0:
            pt.shortcuts.message_dialog(
                title = "NU Login",
                text = "Wrong username or password",
                style = pt.styles.Style.from_dict({
                    "dialog": "bg:#ff0000",
                }),
            )
            continue
        else:
            profile["id"] = values[0][0]
            profile["username"] = values[0][1]
            profile["password"] = values[0][2]
            profile["address"] = values[0][3]
            print(profile)
            showStudentMenu() # enter student menu
            exit()

# student menu
def showStudentMenu():
    while True:
        cursor = connection.cursor()
        cursor.execute("""
                    select distinct temp1.uosCode, temp1.semester, temp1.year, temp1.grade
                    from
                    (select uosCode, semester, year, grade
                    from transcript
                    where studId = %s and grade is null)temp1,
                    (select uosCode, semester, year, grade
                    from transcript
                    where studId = %s and grade is null)temp2
                    where temp1.year > temp2.year
                    and temp1.semester > temp2.semester""", (profile["id"], profile["id"],))
        values = cursor.fetchall()
        print(values)
        cursor.close()
        #today = datetime.date.today()
        courses = list(map(lambda v: (
            v[0],
            v[0] + "    " + v[1] + "    " + str(v[2]) + "   " + str(v[3])
        ), values))

        # build gui

        radioList = pt.widgets.RadioList(courses)
        actions = pt.layout.HSplit([
            pt.widgets.Button("Transcript", lambda: handler("transcript")),
            pt.widgets.Button("Enroll", lambda: handler("enroll")),
            pt.widgets.Button("Withdraw", lambda: handler("withdraw")),
            pt.widgets.Button("Personal Details", lambda: handler("profile"), width = 20),
            pt.widgets.Button("Log out", lambda: handler("logout"))
        ])
        layout = pt.layout.VSplit([
            radioList,
            actions
        ], padding = 1)
        dialog = pt.shortcuts.dialogs.Dialog(
            title = "Welcome, %s. Today is %s-%s semester" % (profile["username"], values[0][2], values[0][1]),
            body = layout,
            with_background=True)

        answer = pt.shortcuts.dialogs._run_dialog(dialog, None)
        #print(answer)
        #cur = [year, semester]
        cur = [values[0][2], values[0][1]]
        if answer == None:
            return
        elif answer == "transcript":
            showTranscript()
        elif answer == "enroll":
            showEnrolment()
        elif answer == "profile":
            showProfile()
        else:
            return

def showTranscript():
    while True:
        cursor = connection.cursor()
        cursor.execute("select uosCode, semester, year, grade from transcript where studId = %s", (profile["id"], ))
        values = cursor.fetchall()
        #print(values)
        cursor.close()
        today = datetime.date.today()
        courses = list(map(lambda v: (
            v[0],
            v[0] + "    " + v[1] + "    " + str(v[2]) + "   " + str(v[3])
        ), values))
        
        
        answer = pt.shortcuts.radiolist_dialog(
            title = "%s's transcript" % profile["username"],
            text = "Select course to see details",
            ok_text = "See detail",
            cancel_text = "Return",
            values = courses
        )
        #print(answer)
        if answer == None:
            return
        else:
            showCourseDetail(answer)
        
        

def showCourseDetail(courseId: str):
    print(courseId)
    cursor = connection.cursor()
    cursor.execute("""
        select uosName
        from unitofstudy
        where uosCode = %s
    """, (courseId, ))
    courseName, = cursor.fetchall()[0]

    cursor.execute("""
        select semester, year, grade
        from transcript
        where studId = %s and uosCode = %s
    """, (profile["id"], courseId))
    semester, year, grade = cursor.fetchall()[0]

    cursor.execute("""
        select uosoffering.enrollment, uosoffering.maxEnrollment, faculty.name
        from uosoffering, faculty
        where uosoffering.uosCode = %s and uosoffering.semester = %s and uosoffering.year = %s and uosoffering.instructorId = faculty.id
    """, (courseId, semester, year))
    enrollment, maxEnrollment, instructorName = cursor.fetchall()[0]

    cursor.close()

    print(courseId, courseName, year, semester, enrollment, maxEnrollment, instructorName)

    answer = pt.shortcuts.message_dialog(
        title = "%s: %s" % (courseId, courseName),
        text = pt.HTML("""
            <b>course id</b> %s \n
            <b>course name</b> %s \n
            <b>year</b> %d \n
            <b>semester</b> %s \n
            <b>enrollment</b> %d \n
            <b>max enrollment</b> %d \n
            <b>instructor name</b> %s \n
            <b>grade</b> %s
        """ % (courseId, courseName, year, semester, enrollment, maxEnrollment, instructorName, grade if grade else "N/A"))
    )
    return

def showEnrolment():
    pass

def showWithdraw():
    pass

def showProfile():
    profile.update(getProfile(profile["id"]))
    text = pt.HTML("""
        <b>student id</b> %s \n
        <b>name</b> %s \n
        <b>address</b> %s \n
        <b>password</b> %s \n
    """ % (profile["id"], profile["username"], profile["address"], profile["password"]))
    actions = pt.layout.HSplit([
        pt.widgets.Button("Change address", lambda: handler("address"), 20),
        pt.widgets.Button("Change password", lambda: handler("password"), 20),
        pt.widgets.Button("Return", lambda: handler("return")),
    ])
    layout = pt.layout.VSplit([
        pt.widgets.Label(text),
        actions,
    ], padding = 1)
    dialog = pt.shortcuts.dialogs.Dialog(
        title = "Peronsal details",
        body = layout,
        with_background=True
    )
    answer = pt.shortcuts.dialogs._run_dialog(dialog, None)

    if answer == "address":
        newAddress = pt.shortcuts.input_dialog(
            title = "Change address",
            text = "New address",
        )
    elif answer == "password":
        newPassword = pt.shortcuts.input_dialog(
            title = "Change password",
            text = "New password",
            cancel_text = 'Cancel', 
        )
        if newPassword == None:
            pt.shortcuts.message_dialog(
                title = "New Password",
                text = "Password update failed",
                style = pt.styles.Style.from_dict(
                    {"dialog":"bg:#ff0000",
                     }),
                )
        cursor = connection.cursor()
        cursor.execute("""
            update student
            set password = %s
            where id = %s
        """, (newPassword, profile["id"]))
        connection.commit()
        cursor.close()
    else:
        return

if __name__ == "__main__":
    try:
        connection = mysql.connector.connect(user="root", password="294811", database="project3-nudb", host="localhost", port=3306)
        main()
    except:
        traceback.print_exc()
        connection.close()
