# Account Geo-Heatmap

### About
A proof of concept for creating geographic maps infused with account data. By presenting the data visually, users can understand not only the geography of their patch, but derive insights through the use of filters, coloring, and important account metrics.

For example, by setting the size of the account marker based on total spend and setting the color of the account marker based on total LDOS, we can identify customers with high spend and high LDOS. Or, we can size by legacy switching and color by Cat 9k switching. 

For example, we can use different data points to color and size the accounts on the map, identifying points of interest at intersections of the user choosing. The following are a few examples, but there are many possibilities:
- Color by Total Spend, Size by Total LDoS (easy hanging fruit, high spend/high ldos)
- Color by legacy switching, Size by Cat 9k switching (the customer may have LDoS, but have they already refreshed?)
- Color by Vertical, Size by Total Spend (who are my top retail, high ed, healthcare customers? Who could we be targeting with campaigns?)
- Color by Catalyst Switching/Wireless/Routing, Size by Security Spend (which customers may be good candidates for ISE, Secure Firewall, etc.)
- Color by Meraki Wireless, Size by Catalyst switching (Unification story, can these customers benefit from simplifying their deployment on one dashboard?)

Alternatively, we can use the maps to understand the partner landscape across your patch. 
- Which partners do the most business and where? 
- What other partners have done similar work near my customer?

And lastly, for SLED account teams, we can infuse even more data using SPOT reports.
- How much business does the city do versus the school district?
- Color by Remaining C2 Funds, Size by Total C2 Funds
- What accounts have majority equipment share with vendors that are no Cisco?

---
### How to Run

_Requires a VAE Ready Report (.xlsb) file and a SPOT Data File (.xlsx)_

To run this app first clone the repository and then open a terminal to the app folder.
```
git clone 
cd /heatmap-code
```

Instantiate your virtual environment.
```
python3 -m venv myvenv
source myvenv/bin/activate
```

Set the following environment variables for the two files listed above.
```
export READY_PATH=path/to/file
export SPOT_PATH=path/to/file
```

Install the requirements
```
pip install -r requirements.txt
```

Run the app:
```
python app.py
```

You can run the app on your browser at http://127.0.0.1:8050


