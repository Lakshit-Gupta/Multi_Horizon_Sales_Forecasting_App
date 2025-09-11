import React from 'react';
import { Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useDataContext } from '../contexts/DataContext';

interface NavigationGuardProps {
  children: React.ReactNode;
  requiredDataUpload?: boolean;
}

const NavigationGuard: React.FC<NavigationGuardProps> = ({ 
  children, 
  requiredDataUpload = true 
}) => {
  const { hasUploadedData } = useDataContext();
  const navigation = useNavigation<any>();
  
  React.useEffect(() => {
    if (requiredDataUpload && !hasUploadedData) {
      Alert.alert(
        'Data Required',
        'Please upload data first before accessing this feature.',
        [
          {
            text: 'OK',
            onPress: () => navigation.navigate('TemplateScreen')
          }
        ]
      );
    }
  }, [hasUploadedData, navigation, requiredDataUpload]);
  
  // Only render children if data requirements are met or if no data is required
  return requiredDataUpload && !hasUploadedData ? null : <>{children}</>;
};

export default NavigationGuard;
