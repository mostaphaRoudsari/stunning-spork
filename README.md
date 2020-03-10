# Openfield MRT & UTCI

This method of calculating the open-field MRT uses the SolarCal module of Ladybug, in conjunction with annual radiation simulation using Radiance. Radiation from the sun, reflected radiation from the ground and diffuse radiation from the sky are combined to create an effective radiant field, then converted into an MRT delta which is added to an MRT for surrounding surface temperature (in an open field this long-wave MRT is surface temperature of the ground.) 

Full documentation for this method is available from https://www.ladybug.tools/ladybug-comfort/docs/_modules/ladybug_comfort/solarcal.html.

 A few packages are required here to get this code running. These are listed in the `requirements.txt` file. Most of them you'll already have on your machine, but for those you don't, try running the following command to install them:
 
 `pip install lbt-ladybug lbt-honeybee ladybug-comfort eppy`

The next step is to fix a dodgy bit of code in Honeybee. All you need to do is comment out some lines in the `./honeybee/radiance/sky` file. You can find this by running the following:

 ```python
from honeybee.radiance.sky import skymatrix
print(skymatrix.__file__)
```

Once you've found the file, just comment out lines [90-91]. The code should then look something like the following:

```python
89    def wea(self, w):
90        # assert hasattr(w, 'isWea'), \
91        #     TypeError('wea must be a WEA object not a {}'.format(type(w)))
92        self._wea = w
```

After that, you should be good to go!