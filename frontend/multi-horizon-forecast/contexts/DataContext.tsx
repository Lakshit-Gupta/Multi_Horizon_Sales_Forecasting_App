import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface DataContextType {
  hasUploadedData: boolean;
  setHasUploadedData: (value: boolean) => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [hasUploadedData, setHasUploadedData] = useState<boolean>(false);
  
  // Check AsyncStorage on load to see if data exists
  useEffect(() => {
    const checkForData = async () => {
      try {
        const forecastData = await AsyncStorage.getItem('forecastData');
        const uploadSuccess = await AsyncStorage.getItem('uploadSuccess');
        const hasUploadedDataFlag = await AsyncStorage.getItem('hasUploadedData');
        
        // Set to true if any of these conditions are met
        const hasData = !!(forecastData || uploadSuccess || hasUploadedDataFlag);
        setHasUploadedData(hasData);
        
        console.log('📊 DataContext check:', {
          forecastData: !!forecastData,
          uploadSuccess: !!uploadSuccess,
          hasUploadedDataFlag: !!hasUploadedDataFlag,
          result: hasData
        });
      } catch (error) {
        console.error('Error checking for forecast data:', error);
      }
    };
    
    checkForData();
  }, []);

  return (
    <DataContext.Provider value={{ hasUploadedData, setHasUploadedData }}>
      {children}
    </DataContext.Provider>
  );
};

export const useDataContext = (): DataContextType => {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useDataContext must be used within a DataProvider');
  }
  return context;
};
