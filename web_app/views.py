from web_app import *
from werkzeug.security import generate_password_hash
import hashlib, binascii
from .send_mail import send_mail
from jinja2 import Environment, FileSystemLoader


@app.route('/')
@login_required #added to prevent from login
def home():
    # get complete email list
    return render_template('home.html');


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' :
        #print("username: ",form.username.data,"\n\n\n");
       # return str(form.username.data)
        user=dict();
        try:
            user = mongo.db.users.find_one({"_id":form.username.data})
        #    print('name: ',user['name'], 'password: ',user['password'])
        except Exception as e:
            return str(e)
        #return user['password']    
        if user and User.validate_login(user['password'], form.password.data):
           # return 'inside'
           # print("data: ",form.password.data)
            if not user["verified"]:
                return "Account has not been activated yet, Please check your mail and verify yourself."
            user_obj = User(user['_id'])
            login_user(user_obj)
            flash("Logged in successfully!", category='success')
            return redirect(request.args.get("next") or url_for("home"))
            #home();
            
        flash("Wrong username or password!", category='error')
    print('here');
    return render_template('login.html', title='login', form=form)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    verified=False;
    if request.method == 'POST':
        
        pass_hash = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        verified = True;
        
        #generate token
        email = form.email.data
        #salt: to make two token with same email (future use, suppose we want token for session also)
        token = serializer.dumps(email,salt='email-confirm')
        
        #send mail(recipient,subject,message)
        confirm_link = url_for('confirm_email',token=token,_external=True)
        msg = 'Your link is {0}'.format(confirm_link)
        email_template = ""
       # os.path.join(SITE_ROOT, 'static', 'email_template.html')
        THIS_DIR = os.path.dirname(os.path.abspath(__file__))
        j2_env = Environment(loader=FileSystemLoader(THIS_DIR),trim_blocks=True)
        email_template = j2_env.get_template('email_template.html').render(action_url=confirm_link);
        
        #print(email_template)
        db_insert_successfull = False;
        # Insert the user in the DB
        try:
            mongo.db.users.insert({"_id": form.username.data, "password": pass_hash, "email": form.email.data,"verified":False})
            db_insert_successfull = True
            #return 'Welcome! Thanks for signing up. Please follow this link in your email to activate your account:'
        except Exception as e:
            if 'duplicate key' in str(e):
                return '<p>A user with that credentials already exist!</p> <p><a style="text-decoration:none" href="/reset/{0}"><del>Reset Account </del> <br/>(DELETE ACCOUNT [temporary feature for testing] [clicking on this link will delete the account)</a></p>'.format(email)
            return  str(e);#"User already present in DB."
        finally:
            if db_insert_successfull:
                req = send_mail(email,"Confirm Email",email_template);
                print('Email Response:')
                print('Status: {0}'.format(req.status_code))
                print('Body:   {0}'.format(req.text))
                print('-------------------')
                if 200 == req.status_code:
                    return '<p>Welcome! Thanks for signing up.</p><p>We have sent an email to your email address <b>{0}</b> so with any luck the great guardians<br /> of the internet will deliver this message to your <b>inbox</b>, or <b>spam</b> folder if you are lucky.</p><p>Please note, that the confirmation link will expire after 24 hours.</p> <p> <a href="/login">Click here </a> to go back to login page.'.format(email)
                else:
                    mongo.db.users.remove({"_id": form.username.data})
                    return "<p>Insertion succesfull but couldn't connect to mail server to send mail <br/><b>(devnote: this is really really really bad, check if mail server is setup properly & credentials are correct)</b></p><p>Launcing Failsafe sequence</p> <p> Removing the user from database</p> <p>Please check logs to see what went wrong!"
        #user = mongo.db.users.find_one({"_id": form.username.data})
        
        
        
    
    return render_template('signup.html', title='signup', form=form)



@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=1440) #age is 1440 seconds
        mongo.db.users.update({"email":email},{ "$set": {"verified":True}},False, True);
        #.update({condField: 'condValue'}, { $set: { dateField: new Date(2011, 0, 1)}}, false, true);
    except SignatureExpired:
        return "The token is expired"
    except BadTimeSignature:
        return "The token was not recognised"
    return '<p><b>Verification successful</b></p><p><a href="/login">Go to login </a></p>'


@app.route('/reset/<email>', methods=['GET', 'POST'])
def reset(email):
    mongo.db.users.remove({"email":email})
    return '<p><del>Thanks for your request.</del></p><p><del>We have sent an email to your email address <b>{0}</b></del>. <p><del>Please click on the link in the mail to reset your account.</del></p><p><b>[DEV NOTE: CURRENTLY THIS DOESNT RESETS BUT DELETES THE ACCOUNT (temp feature)]<b></p> <p><br/>Deleted Succesfully</p></br><p><a href="/signup">Go back</a></p>'.format(email)




@app.route('/inner', methods=['GET', 'POST'])
@login_required
def inner():
    global ic
    name = request.form['name']
    password = request.form['password']
    if name == "" or password == "":
        return render_template('index.html');
    else:
        # Reading the file everytime will degrade the function performance
       # df = pd.read_csv("login.csv", sep=',', encoding="utf-8")
        #for index,row in df.iterrows():
        #    if row['name'] == name and row['password'] == password:
         #       print('sucess')
         #       return render_template('inner.html');
        data = "       PLEASE ENTER VALID USERNAME AND PASSWORD TO LOGIN               "
        return render_template('index.html', records=data, title='User');

@app.route('/email', methods=['POST'])
@login_required
def handle_email():
    email = request.form['email']
    url = "http://spiderapi.herokuapp.com/api/emails/"
    print("requesting: ", url)
    headers = {'Content-type': 'application/json'}
    r = requests.post(url, json={"email": email, "key": "C88B933A691E16C56EBC92BCC9A7E"}, headers=headers)
    print(r.json())
    if r.status_code == 200:
        return jsonify(r.json()), 200
    else:
        return jsonify({"response": " Something when wrong ", "status_code": 400});


@app.route('/emails', methods=['GET', 'POST'])
@login_required
def handle_emailList():
    if request.method == 'GET':
        return "Hello getter"
    elif request.method == 'POST':
        req_id = 'file' + datetime.now().strftime(FORMAT)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            try:
                email_list = parse_csv(UPLOAD_FOLDER + filename)
                # print("init.py: email list: ",email_list[0])
                print("init.py: Email list length: ", len(email_list))
                for i in email_list:
                    print(i)
                email_list = [email for email in email_list if email['email'] is not '']
                list_size = len(email_list);
                req_id += '_{0}'.format(list_size);
                print("parsed length:", list_size)
                executor.submit(parse_csv_pool, email_list, req_id)
                return redirect(url_for('results', rid=req_id))
                # return 'One jobs was launched in background with id: {0}'.format(req_id)
            except Exception as e:
                return str(e);
        else:
            return jsonify({'code': 400, 'message': 'No interface defined for URL'}), 400


@app.route('/results', methods=['GET'])
@login_required
def results():
    req_id = request.args['rid']
    return render_template('result.html', req_id=req_id);


@app.route('/guess', methods=['GET', 'POST'])
@login_required
def guess_email():
    if request.method == 'POST':
        req_id = 'file' + datetime.now().strftime(FORMAT)
        fname = request.form['fname']
        lname = request.form['lname']
        dname = request.form['dname']
        e = EmailPermutator()
        email_list = e.get_emails(fname=fname, lname=lname, dname=dname)
        for i, email in enumerate(email_list):
            email_list[i] = {'email': email}
        list_size = len(email_list);
        req_id += '_{0}'.format(list_size);
        print("parsed length:", list_size)
        executor.submit(parse_csv_pool, email_list, req_id)
        # return jsonify({"response":req_id,"url":'/results?rid='+req_id});
        return redirect(url_for('results', rid=req_id))
    return "Hello"


def recursive_len(item):
    if type(item) == list:
        return sum(recursive_len(subitem) for subitem in item)
    else:
        return 1


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/getuser', methods=['POST'])
def getuser():
    iname = request.form['iname']
    iemail = request.form['iemail']
    ipassword = request.form['ipassword']
    if (iname == "" or iemail == "" or ipassword == ""):
        return render_template('index.html');
    else:
       # df = pd.read_csv("login.csv", sep=',', encoding="utf-8")
        #df2 = df.append(pd.DataFrame([[iname, ipassword, iemail]], columns
    #    =df.columns))
     #   df2.to_csv("login.csv", index=False)
      #  print()
        data = "       USER SUCESSFULLY CREATED NOW YOU CAN LOGIN               "
        return render_template('index.html', records=data, title='User');


@app.route('/guesses', methods=['GET', 'POST'])
def handle_guessList():
    if request.method == 'GET':
        return "Hello getter"
    elif request.method == 'POST':
        req_id = 'guess' + datetime.now().strftime(FORMAT)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            try:
                guess_list = parse_csv(UPLOAD_FOLDER + filename)
                print("init.py:/guesses: Email list length: ", len(guess_list))
                # print("init.py:/guesses: email list: ",guess_list[0])

                # for i in guess_list:
                #     print(i)
                if ('firstname' not in guess_list[0].keys()):
                    return 'firstname column not present in csv!';
                elif ('lastname' not in guess_list[0].keys()):
                    return 'lastname column not present in csv!';
                elif ('domain' not in guess_list[0].keys()):
                    return 'domain column not present in csv!';

                e = EmailPermutator();
                # print("init.py:/guesses: type of list[0]",type(guess_list[0]));
                tmp_list = guess_list;
                for person in tmp_list:
                    person['email'] = e.get_emails(person['firstname'], person['lastname'], person['domain']);

                tmp_emails = [];
                for person in tmp_list:
                    each_persons_list = []
                    for email in person['email']:
                        tmp_person = person.copy();
                        tmp_person['email'] = email;
                        each_persons_list.append(tmp_person);
                    tmp_emails.append(each_persons_list);

                print("type: tmp_emails[0]", type(tmp_emails[0]));

                # tmp_emails2 = [[person.copy()] for person in tmp_list for email in person['email']]
                # print("tmp_emails2",len(tmp_emails2));
                # print("#################");
                # print("init.py: tmp_list: ");
                # print(tmp_emails);
                # print("##################");

                #  email_list = [{'firstname':client['firstname'],'lastname':client['lastname'],'domain':client['domain'],'emails':e.get_emails(client['firstname'],client['lastname'],client['domain'])} for client in guess_list];
                #  emails = [[{'email':i,'firstname':client['firstname'],'lastname':client['lastname'],'domain':client['domain']} for i in client['emails']] for client in email_list]
                list_size = recursive_len(tmp_emails);
                req_id += '_{0}'.format(list_size);
                executor.submit(guess_pool, tmp_emails, req_id)
                # return redirect(url_for('results',rid=req_id))
                # return 'One jobs was launched in background with id: {0}'.format(req_id)
                # return str(emails);
                return redirect(url_for('results', rid=req_id))
            except Exception as e:
                print(e);
                return 'Guesses:Something went wrong while parsing, Error: ' + str(e);
        else:
            return jsonify({'code': 400, 'message': 'No interface defined for URL'}), 400


@app.route('/singleD', methods=['GET', 'POST'])
@login_required
def one_domain():
    if request.method == 'POST':
        req_id = 'file' + datetime.now().strftime(FORMAT)
        cname = request.form['cname']
        data = clearbit.NameToDomain.find(name=cname)
        flash(data)
        '''for i, email in enumerate(email_list):
            email_list[i] = {'email': email}
        list_size = len(email_list);
        req_id += '_{0}'.format(list_size);
        print("parsed length:", list_size)
        executor.submit(parse_csv_pool, email_list, req_id)
        #return jsonify({"response":req_id,"url":'/results?rid='+req_id});
        return redirect(url_for('results', rid=req_id))'''
    return "Hello"

@lm.user_loader
def load_user(username):
    u = mongo.db.users.find_one({"_id": username})
    if not u:
        return None
    return User(u['_id'])
