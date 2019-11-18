from typing import *
import mysql.connector
import prompt_toolkit as pt
import datetime
import traceback

profile = {}
cur = {}

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
            cur = {}
            #print(profile)
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
            title = "Welcome, %s. Today is %s-%s Semester" % (profile["username"], values[0][2], values[0][1]),
            body = layout,
            with_background=True)

        answer = pt.shortcuts.dialogs._run_dialog(dialog, None)
        #print(answer)
        #cur = [year, semester]
        #cur = [values[0][2], values[0][1]]
        cur['year'] = values[0][2]
        cur['semester'] = values[0][1]
        
        if answer == None:
            return
        elif answer == "transcript":
            showTranscript()
        elif answer == "enroll":
            showEnrollment()
        elif answer == "profile":
            showProfile()
        elif answer == "withdraw":
            showWithdraw()
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

def showEnrollment():
    #print(cur)
    if cur['semester'] == "Q2":
        tempy = cur['year'] + 1
        tempq = "Q1"
    elif cur['semester'] == "Q1":
        tempy = cur['year']
        tempq = "Q2"
    while True:
        cursor = connection.cursor()
        cursor.execute("""
                select *
                from lecture
                where (year = %s and semester = %s)
                or (year = %s and semester = %s)""",  \
                (cur['year'], cur['semester'], tempy, tempq, ))
        values = cursor.fetchall()
        #print(values)
        cursor.close()
        #today = datetime.date.today()
        courses = list(map(lambda v: (
            v[0],
            v[0] + "    " + v[1] + "    " + str(v[2]) + "   " + str(v[3]) + "   " + str(v[4])
        ), values))
        
        
        answer = pt.shortcuts.radiolist_dialog(
            title = "%s-%s Lecture" % (cur['year'], cur['semester']),
            text = "Lectures available for this and next semester are listed",
            ok_text = "Select",
            cancel_text = "Return",
            values = courses
        )
        #print(answer)
        if answer == None:
            return
        else:
            #print(answer)
            confirm = pt.shortcuts.yes_no_dialog(
                title = 'Confirm',
                text = 'Do you want to select %s?' % (answer, ))
            
            if confirm:
                p_out = 0
                cursor = connection.cursor()
                
                cursor.execute("""
                drop procedure if exists check_enroll""")
                cursor.execute("""
                create procedure check_enroll(out p_out int, in lec_code char(8), in stu_id int,
                                                                          in year_in int, in semester_in char(2))
                begin
                declare req_cnt decimal default 0;
                declare pre_cnt decimal default 0;
                declare enroll decimal default 0;
                declare max_en decimal default 0;

                select count(requires.prerequoscode)
                into req_cnt
                from requires
                where requires.uoscode = lec_code;

                select count(transcript.uoscode)
                into pre_cnt
                from transcript, requires
                where requires.uoscode = lec_code
                and studID = stu_id
                and requires.prerequoscode = transcript.uoscode
                and transcript.grade is not null;

                select enrollment, maxenrollment
                into enroll, max_en
                from uosoffering
                where uoscode = lec_code
                and year = year_in
                and semester = semester_in;

                  if exists(select *
                                        from transcript
                                        where studID = 3213
                                        and uoscode = lec_code)
                  then
                      set p_out=1;
                  elseif (req_cnt > pre_cnt)
                  then
                          set p_out = 2;
                  elseif (enroll >= max_en)
                  then
                      set p_out = 3;
                  else
                          set p_out = 4;
                      
                      insert into transcript
                      values(stu_id, lec_code, semester_in, year_in, null);
                      
                      update uosoffering
                          set enrollment = enrollment + 1
                          where uoscode = lec_code
                          and year = year_in
                          and semester = semester_in;
                  end if;
                  select @p_out;
                  end""")
                
                args = (p_out, answer, profile['id'], cur['year'], cur['semester'])
                args = cursor.callproc(
                'check_enroll', args)
                #connection.commit()
                cursor.close()
                #Judge Duplicate
                print(args)
                p_out = args[0]
                
                if p_out == 1:
                    pt.shortcuts.message_dialog(
                    title = "Lecture Selection Failed",
                    text = "Cannot Select Duplicate Lectures!",
                    style = pt.styles.Style.from_dict({
                    "dialog": "bg:#ff0000",
                    }),)
                    continue
                
                #Judge prerequsite
                
                elif p_out == 2:
                    cursor = connection.cursor()
                    cursor.execute("""
                        select requires.prerequoscode
                        from requires
                        where requires.uoscode = %s""",  \
                        (answer, ))
                    req = cursor.fetchall()
                    #print(req)
                    cursor.close()
                    reqmsg = ''
                    
                    for cl in req:
                        reqmsg += str(cl).replace("("," ").replace(")","").replace(","," ")
                    pt.shortcuts.message_dialog(
                    title = "Lecture Selection Failed",
                    text = "To Select %s, You Should Complete%s First!" % (answer, reqmsg, ),
                    style = pt.styles.Style.from_dict({
                    "dialog": "bg:#ff0000",
                    }),)
                    continue
                
                #Judge maxenrollment
                
                elif p_out == 3:
                    cursor = connection.cursor()
                    cursor.execute("""
                        select enrollment, maxenrollment
                        from uosoffering
                        where uoscode = %s
                        and year = %s
                        and semester = %s""",  \
                        (answer, cur['year'], cur['semester']))
                    judge3 = cursor.fetchall()
                    cursor.close()
                    
                    pt.shortcuts.message_dialog(
                    title = "Lecture Selection Failed",
                    text = "%s is Full Now(%s/%s)!" % (answer, judge3[0][0], judge3[0][1]),
                    style = pt.styles.Style.from_dict({
                    "dialog": "bg:#ff0000",
                    }),)
                    continue
                #All cases passed, now update information
                elif p_out == 4:
                    pt.shortcuts.message_dialog(
                    title = "Lecture Selection Succeed",
                    text = "Congratulations! You Have Selected %s Succesfully!" % (answer, ),
                    style = pt.styles.Style.from_dict({
                    "dialog": "bg:#00ff00",
                    }),)
                    continue
                else:
                    raise ValueError("Wrong P_OUT!")
            
            pass
            

def showWithdraw():
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
        
        
        answer = pt.shortcuts.radiolist_dialog(
            title = "%s-%s Lecture" % (cur['year'], cur['semester']),
            text = "Lectures you have chosen for this semester are listed",
            ok_text = "Withdraw",
            cancel_text = "Return",
            values = courses
        )
        #print(answer)
        if answer == None:
            return
        else:
            #print(answer)
            confirm = pt.shortcuts.yes_no_dialog(
                title = 'Confirm',
                text = 'Do you want to withdraw %s?' % (answer, ))
            
            if confirm:
                cursor = connection.cursor()
                cursor.execute("""
                drop procedure if exists check_withdraw""")
                cursor.execute("""
                create procedure check_withdraw(in lec_code char(8), in stu_id int,
                                                                          in year_in int, in semester_in char(2))
                begin
                      delete from transcript
                          where StudId = stu_id and UoSCode = lec_code
                      and Semester = semester_in and year = year_in;
                      
                      update uosoffering
                          set enrollment = enrollment - 1
                          where uoscode = lec_code
                          and year = year_in
                          and semester = semester_in;
                end""")
                args = (answer, profile['id'], cur['year'], cur['semester'])
                args = cursor.callproc(
                'check_withdraw', args)
                #connection.commit()
                #trigger
                cursor.close()
                pt.shortcuts.message_dialog(
                    title = "Lecture Withdraw Succeed",
                    text = "Congratulations! You Have Withdrawn %s Succesfully!" % (answer, ),
                    style = pt.styles.Style.from_dict({
                    "dialog": "bg:#00ff00",
                    }),)

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
            cancel_text = 'Cancel',
        )
        cursor = connection.cursor()
        cursor.execute("""
            update student
            set address = %s
            where id = %s
        """, (newAddress, profile["id"]))
        #connection.commit()
        cursor.close()
    elif answer == "password":
        newPassword = pt.shortcuts.input_dialog(
            title = "Change password",
            text = "New password",
            cancel_text = 'Cancel', 
        )
        if newPassword == None:
            pt.shortcuts.message_dialog(
                title = "New Password Failed",
                text = "Password Should Not be NULL!",
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
        #connection.commit()
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
