# Earthporn Showerthoughts

Setup in terminal:
```shell
git clone https://github.com/scul86/earthporn_showerthoughts.git
cd earthporn_showerthoughts 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Change the file paths in `ep_st.config` for:
- `template`: where you have stored the template (should be the same folder)
- `display`:  where you want the output file (ep_st.html)
- `log`:      where to put the error and event log files.  

default location for all 3 above is the same folder as 'ep_st.py

If desired, set the display_path to somewhere accessible by your webserver, otherwise does not matter
Run the python3 script (from the containing folder: `./ep_st.py`)
Go to the output file, and display it in your webbrowser.

Feel free to tinker with the settings (minSize, number of posts to get, etc...)