# GroupLoop
Human Computer Interaction Final Project

Windows instructions for setting up the app locally

1. If you do not have .venv installed, first create the virtual environment locally by running:  python -m venv venv

2. After this is done, you need to activate the virtual environment. You can do this with the command: venv\Scripts\activate
    * If you are on macOS, after step one you will instead use the command source venv/bin/activate

You will know that it is activated because you'll see the (venv) tag show up in your terminal. Virtual environments are a way to install and manage dependencies on a per-project basis instead of installing the modules globally.

3. You can install dependencies one of two ways. The easiest is to have a requirements.txt file available. Just run the command: pip install -r requirements.txt

4. The other way is to use a command like 'pip install package' for whatever you want. If we add packages to this project and we want to make them part of the requirements list for easy install, just use the command:  pip freeze > requirements.txt

5. To run the app inside your new virtual environment with dependencies installed, simply type the command:  python app.py

6. It will display your local IP and a port. Just visit it in the browser to interact with your app, e.g., http://127.0.0.1:5000
----------------------------------------------------------------

7. If you are using VSCode and getting errors about things like wtforms, pymysql, etc not able to be resolved from source, double check that you've installed them in your virtual environment. Activate the virtual environment with the command from step 2, then type: pip show modulename

If you get text that shows the module information, it is installed and you just need to change your Python interpreter. Press Ctrl+Shift+P and type Python Select Interpreter. There will be a selection for it. Click on it and click the same interpreter for your workspace, which will likely also be the recommended one.
