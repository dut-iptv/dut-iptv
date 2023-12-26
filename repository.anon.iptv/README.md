## repository.anon.iptv

### **Notice: API Updates and Alpha Releases**
Currently, nearly all providers have changed their APIs or something else happened that rendered those add-ons unusable. I do not have contact with the original developer, and it will take some time to get through all the add-ons. I only have access to Ziggo GO and are unable to fix other add-ons without having access to other accounts. Ziggo GO now works again and is released as an Alpha version. If all goes well, I'm planning to try to get KPN iTV and possibly Videoland working again. Unfortunately, I do not have access to anything regarding Dut-EPG, this means that anything replay and VOD related does not work for the time being. On the other hand, I was able to add a feature to watch recordings from Ziggo GO. I hope to add such alternatives to compensate for replay, until I figure out Dut-EPG. If anyone has any idea, feel free to create an issue with the 'enhancement' tag. 

### About

-Watch ~CanalDigitaal~/~F1 TV~/KPN/~NLZiet~/~Telenet (BE)~/~Telfort~/~T-Mobile~/~Videoland~/~XS4ALL~/Ziggo Live TV and content from anywhere in the EU

### Features

-Unofficial 3rd Party repo and plugins for Kodi

-Watch live TV for supported channels in your subscription

-~Replay programs from the last 7 days for supported channels in your subscription~

-Watch video on demand (VOD) content

-~Search content~

-Supports watching TV and listening to radio using the IPTV Simple PVR Addon

-Supports catchup using IPTV Simple PVR Addon (through the separate Dut-IPTV Simple IPTV Connector addon)

### Maximum supported Resolution

- ~CanalDigitaal: 1080P~
- ~F1 TV: 1080P (50hz)~
- ~KPN/Telfort/XS4ALL: 1080P~
- ~NLZiet: 1080P~
- ~Telenet (BE): 720P~
- ~T-Mobile: 1080P~
- ~Videoland: 1080P~
- Ziggo: 720P

### Required

-Subscription to any of the supported providers (not free)

-Kodi 20 or higher with Widevine Support (free)

  **[Note: Kodi 19 might still work, but will no longer be taken into account in future updates]**

### Installation
Instructions adopted from the kodi wiki, see [HOW-TO:Install add-ons from zip files](https://kodi.wiki/view/HOW-TO:Install_add-ons_from_zip_files)

-Step 1: Download the repository.anon.iptv ZIP-file from [here](https://github.com/QuasarKodearring/QuasarKodearring.github.io/raw/master/repository.anon.iptv-latest.zip)

-Step 2: To access the Add-on browser see: [How to access the Add-on browser](https://kodi.wiki/view/Add-on_manager#How_to_access_the_Add-on_browser) or [How to access the Add-on manager](https://kodi.wiki/view/Add-on_manager#How_to_access_the_Add-on_manager)

-Step 3: Select Install from zip file

-Step 4: If you have not enabled Unknown Sources, you will notified that it is disabled. If you wish to enable select Settings, if you do not wish to enable select OK. If you have already enabled Unknown sources skip to Step 7.

-Step 5: When you select Settings you will be taken to the Add-ons settings window. Enable Unknown sources if you wish to install your add-on or repository from a zip file.

-Step 6: After you enable Unknown sources you will be presented with a Warning. Make sure you read and understand this warning, then select Yes if you wish to proceed.

-Step 7: If you have selected Yes and enabled Unknown sources you can then navigate back to the Add-on browser and once again select Install from zip file

-Step 8: You will now be presented with a browser window where you can navigate to where your zip file is stored. Your zip file can be stored anywhere your device has access to and can be either on local storage or a network share.

-Step 9: Once you have navigated to the zip file you downloaded in Step 1, select it then select OK. You will be notified when the repository is installed succesfully.

-Step 10: Navigate back to the Add-on browser and select Install from repository

-Step 11: Navigate to Dutch IPTV Repository

-Step 12: Navigate to Video add-ons

-Step 13: Select one or more of the available addons to install, dependencies will automatically be installed

### Additional instructions for general Linux / OSMC

- The addons require the pycryptodomex packages, which is not included in OSMC and possibly general linux distributions

- These steps are not required for CoreELEC/LibreELEC/Windows/Android

- Execute the following commands in a terminal:

```
sudo apt-get install python3-crypto
sudo apt-get install build-essential python3-pip
sudo python3 -m pip install -U setuptools
sudo python3 -m pip install wheel
sudo python3 -m pip install pycryptodomex
```

### Known Bugs

- See [Known Bugs](https://github.com/3DSBricker/dut-iptv/discussions/1)

### Wanted Features / Enhancements

- See [Wanted Features](https://github.com/3DSBricker/dut-iptv/discussions/2)

### Source code / Release information / Issues / PR's / Discussions

- See https://github.com/3DSBricker/dut-iptv

### Thanks

-dut-iptv for this great addon

-Matt Huisman for his development of the kodi addons that where used as a base for this addon

-peak3d for Inputstream Adaptive

-phunkyfish for IPTV Simple PVR

-Team Kodi for Kodi