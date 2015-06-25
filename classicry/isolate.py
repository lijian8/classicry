def isolate_cries(sDir, iResample = 8000, bSave = False, sCutDir=None, iSigmaSecs=0.05):
    """
    expected peak corrolation by convolution, then edge detection
    iResample = 8000 Hz resampling rate
        Hard coded variables obtained by trial:
            linerar smoothing coefficient:  iLinearSmooth = 20 frames
            minima threshhold factor:  iThreshFact = 10 times
            horozontal cluster threshhold:  iThreshCluster = 0.01 seconds * iSampleRate
            keep sections threshhold factor:  iThreshKeepFact = 5
    can save each cut to separate file 
    returns list of cuts, each cut is peak data (correlation with gaussian)
    """
    import numpy as np
    from scipy import signal
    import common_fxns
    
    iLinearSmooth = 50
    
    (iSampleRate, 
        aTime, 
        aAudio, 
        aCorr,
        aOrigAudio) = common_fxns.process_dir(sDir, iSmooth=iLinearSmooth, iResample=iResample, iSigmaSecs=iSigmaSecs)
    
    
    iThreshFact = 10
    iThreshClusterSecs = 0.01
    iThreshCluster = iThreshClusterSecs * iSampleRate
    iThreshKeepFact = 4
    
    
    from scipy import ndimage
    aFirstDeriv = ndimage.sobel(aCorr)
    
    aFirstDeriv = common_fxns.smooth(aFirstDeriv, iLinearSmooth)
    aSecondDeriv = ndimage.sobel(aFirstDeriv)
    
    
    
    
    
    #---Get minima and filter
    #intersecion of derivative with zero line (get maxima and minima)
    aZero = np.zeros(np.shape(aSecondDeriv))
    iTolerance = 1.0        #tolerance to zero-intersect
    aZeroIntersect = np.argwhere(np.isclose(aZero, aFirstDeriv, atol=iTolerance)).reshape(-1)
    
    #positive second derivitave (get minima)
    aMinimaIndeces = np.array([ i for i in aZeroIntersect if aSecondDeriv[i] > 0 ])
    
    
    #apply threshold filter for minima (y axis filter)
    iMax = np.max(aCorr)
    iMin = np.min(aCorr)
    iAmplThresh = (iMax - iMin)/iThreshFact      #we only want to keep low minima
    aMinimaIndeces = np.array( [i for i in aMinimaIndeces if aCorr[i] < iAmplThresh] )
    
    
    #apply proximity filter to single out consecutive groups of minima
    lMinimaIndeces = []
    for i in range(len(aMinimaIndeces) - 1):
        if aMinimaIndeces[i+1] - aMinimaIndeces[i] > iThreshCluster:
            lMinimaIndeces.append(aMinimaIndeces[i])
    
    lMinimaIndeces.append(aMinimaIndeces[-1])
    aMinimaIndecesFilt = np.array(lMinimaIndeces)
    
    
    #add the beginning and end of the track
    aMinimaIndecesFilt = np.insert(aMinimaIndecesFilt,0, 0)
    aMinimaIndecesFilt = np.insert(aMinimaIndecesFilt, len(aMinimaIndecesFilt), len(aCorr)-1)
    
    
    #get time values from indeces
    aTimeIntersects = np.array(aTime)[aMinimaIndecesFilt]
    
    
    
    
    
    #cut up audio according to minima indeces
    iMin = 1
    iCut = 1
    
    laAudios = []
    laCorrs = []
    
    ##TODO remove
    #lKeep = []
    #lThrow = []
    #iMax = np.max(aCorr)
    #lStart = []
    
    while iMin < len(aMinimaIndecesFilt):
        iStart = aMinimaIndecesFilt[iMin -1]
        iEnd = aMinimaIndecesFilt[iMin]
        
        ##TODO remove
        #iMean = iStart + (iEnd-iStart)/2
        #iMeanTime = iMean/iSampleRate
        #lStart.append(iStart/iSampleRate)
        
        aAudioCut = np.array(aAudio[iStart : iEnd])
        aCorrAudioCut = np.array(aCorr[iStart : iEnd])
        aOrigAudioCut = np.array(aOrigAudio[iStart : iEnd])
        
        bKeep = (np.max(aCorrAudioCut) - np.min(aCorrAudioCut)) > np.max(aCorr)/iThreshKeepFact
        
        #throw away sections with max amplitude less than max/iThreshKeepFact
        if bKeep:
            if bSave:
                sDirCutNum = '{0}/cut{1}.wav'.format(sCutDir, iCut)
                from scipy.io.wavfile import write
                write(sDirCutNum, iSampleRate, aOrigAudioCut)
            
            laAudios.append(aAudioCut)
            laCorrs.append(aCorrAudioCut)
            
            
            iCut += 1
            
            ##TODO remove
            #lKeep.append(iMeanTime)
        #else:
            #lThrow.append(iMeanTime)
        
        
        iMin += 1
    
    
    
    
    #def normalize(aArray):
        #iMax = np.max(aArray)
        #return [i/iMax for i in aArray]
    
    #iMax = 1
    #aCorr = normalize(aCorr)
    #aAudio = normalize(aAudio)
    #aFirstDeriv = normalize(aFirstDeriv)
    #aSecondDeriv = normalize(aSecondDeriv)
    ##aOrigAudio = normalize(aOrigAudio)
    
    #import matplotlib.pyplot as plt
    #plt.figure(1)
    
    #sType = sDir.split('/')[-1].split('_')[0].split('-')[0]
    
    #plt.subplot(2,1,1)
    #plt.title('{}, Blue:  Corr, Red:  Audio,   green:original'.format(sType))
    #plt.plot(aTime, aCorr, 'b')
    #plt.plot(aTime, aAudio, 'r')
    #plt.plot(aTime, aOrigAudio, 'g')
    #plt.plot(lKeep, [iMax/3 for i in range(len(lKeep))], 'g^')
    #plt.plot(lThrow, [iMax/3 for i in range(len(lThrow))], 'rx')
    #plt.plot(lStart, [iMax/50 for i in range(len(lStart))], 'yo')
    
    ##print np.max(aOrigAudio)
    #plt.subplot(2,1,2)
    #plt.plot(aOrigAudioCut)
    
    ##plt.subplot(2,1,2)
    ##plt.title('Green: Orig, Blue:  1st, Red:  2nd')
    ##plt.plot(aTime, aCorr, 'g')
    ##plt.plot(aTime, aFirstDeriv, 'b')
    ##plt.plot(aTime, aSecondDeriv, 'r')
    ##plt.plot(lKeep, [0 for i in range(len(lKeep))], 'g^')
    ##plt.plot(lThrow, [0 for i in range(len(lThrow))], 'rx')
    ##plt.plot(lStart, [0 for i in range(len(lStart))], 'yo')
    
    
    #plt.show()
    
    
    
    
    
    
    
    
    return iSampleRate, laAudios, laCorrs

















    












