// Updated version of the TemplateScreen.tsx file for Google Cloud backend
// Removed AWS references and updated to use GCP API endpoints

import * as React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import AsyncStorage from '@react-native-async-storage/async-storage';
import XLSX from 'xlsx';
import { useNavigation } from '@react-navigation/native';
import { forecastApi, gcpApi } from '../api/api'; // Import GCP API instead of AWS
import { getAuthToken } from '../services/auth';
import { useDataContext } from '../contexts/DataContext';

const TemplateScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const { setHasUploadedData } = useDataContext();
  const [modalVisible, setModalVisible] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [gcpHealthy, setGcpHealthy] = React.useState(false);

  // Check GCP health on component mount
  React.useEffect(() => {
    checkGCPHealth();
  }, []);

  const checkGCPHealth = async () => {
    try {
      const response = await gcpApi.checkHealth();
      setGcpHealthy(response.status === 'healthy');
    } catch (error) {
      console.log('GCP backend not available, check your network connection');
      setGcpHealthy(false);
    }
  };
  
  const validateExcelData = (data: any[]): boolean => {
    if (!data || data.length !== 37) return false;

    const requiredColumns = ['date', 'history', 'onpromotion', 'is_holiday', 'transactions', 'store_nbr', 'item_nbr'];
    const firstRow = data[0];

    return requiredColumns.every((col) => Object.keys(firstRow).includes(col));
  };

  const uploadFile = async () => {
    if (uploading) return;
    setUploading(true);
    
    try {
      // Use minimal API (preferred) if available, otherwise fall back to original
      if (gcpHealthy) {
        await uploadFileGCP();
      } else {
        Alert.alert('Connection Error', 'Cannot connect to the API. Please check your internet connection and try again.');
      }
    } catch (error: any) {
      console.error('Upload failed:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to upload file. Please ensure you are logged in and try again.');
    } finally {
      setUploading(false);
    }
  };

  const uploadFileGCP = async () => {
    try {
      // Step 1: Select the file
      console.log('Requesting file selection...');
      const result = await DocumentPicker.getDocumentAsync({
        type: [
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'application/vnd.ms-excel',
        ],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const { uri, name, mimeType } = result.assets[0];
        console.log(`Selected file: ${name}`);
        
        // Step 2: Validate the file contents first
        try {
          console.log('Validating file contents...');
          const fileContent = await FileSystem.readAsStringAsync(uri, {
            encoding: FileSystem.EncodingType.Base64,
          });
          
          const workbook = XLSX.read(fileContent, { type: 'base64' });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          
          if (!validateExcelData(jsonData)) {
            Alert.alert('Invalid File', 'Excel file must have exactly 37 rows and required columns: date, history, onpromotion, is_holiday, transactions, store_nbr, item_nbr.');
            return;
          }
          console.log('File validation successful - correct format detected');
        } catch (validationError) {
          console.error('File validation error:', validationError);
          Alert.alert('Invalid File', 'Could not read the Excel file. Please make sure it is a valid .xlsx file with the correct format.');
          return;
        }
        
        // Step 3: Upload file to minimal API
        console.log('Uploading file to minimal API...');
        const fileName = name || `upload_${new Date().toISOString().replace(/[-:.]/g, '')}.xlsx`;
        
        const uploadResponse = await gcpApi.uploadFile(
          uri, 
          fileName,
          mimeType || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        );
        
        console.log('Upload response:', uploadResponse);
        
        // Step 4: After successful upload, request forecast
        if (uploadResponse && uploadResponse.success) {
          console.log('Upload confirmed successful, updating data context...');
          
          // Always update DataContext when upload succeeds
          setHasUploadedData(true);
          await AsyncStorage.setItem('uploadSuccess', 'true');
          await AsyncStorage.setItem('hasUploadedData', 'true');
          
          console.log('Requesting forecast after successful upload...');
          
          try {
            const forecastData = {
              forecast_days: 7,
              history_data: [], // Empty - use uploaded data
              is_holiday: [0, 0, 0, 0, 0, 0, 0],
              onpromotion: [0, 0, 0, 0, 0, 0, 0],
              store_nbr: 1,
              item_nbr: 1
            };
            
            const forecastResponse = await gcpApi.submitForecastRequest(forecastData);
            console.log('Forecast response:', forecastResponse);
            
            if (forecastResponse && forecastResponse.success && forecastResponse.forecast) {
              // Store forecast data for use in ForecastScreen
              const predictions = forecastResponse.forecast;
              await AsyncStorage.setItem('forecastData', JSON.stringify(predictions));
              await AsyncStorage.setItem('uploadSuccess', 'true');
              
              // Update DataContext to reflect that data has been uploaded
              setHasUploadedData(true);
              
              Alert.alert(
                'Success', 
                'File uploaded and forecast generated successfully! View your forecast now.',
                [{ text: 'OK', onPress: () => {
                  setModalVisible(false);
                  navigation.navigate('EnterDetailsScreen');
                }}]
              );
            } else {
              // File uploaded successfully but forecast failed
              // Still update DataContext since file upload worked
              setHasUploadedData(true);
              await AsyncStorage.setItem('uploadSuccess', 'true');
              
              Alert.alert('Error', 'File uploaded successfully but forecast generation failed. Please try again.');
            }
          } catch (forecastError: any) {
            console.error('Forecast error:', forecastError);
            
            // File uploaded successfully but forecast failed
            // Still update DataContext since file upload worked
            setHasUploadedData(true);
            await AsyncStorage.setItem('uploadSuccess', 'true');
            
            Alert.alert(
              'Upload Successful', 
              'File was uploaded successfully, but forecast generation failed. Please enter item and store details to continue.',
              [{ text: 'OK', onPress: () => {
                setModalVisible(false);
                navigation.navigate('EnterDetailsScreen');
              }}]
            );
          }
        } else {
          Alert.alert('Error', 'Failed to upload file. Please check your connection and try again.');
        }
      } else {
        console.log('File selection cancelled or failed');
        Alert.alert('Cancelled', 'No file selected.');
      }
    } catch (error: any) {
      console.error('GCP upload error:', error);
      throw error;
    }
  };

  const uploadFileOriginal = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: [
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'application/vnd.ms-excel',
        ],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const { uri, name } = result.assets[0];
        const fileContent = await FileSystem.readAsStringAsync(uri, {
          encoding: FileSystem.EncodingType.Base64,
        });

        const workbook = XLSX.read(fileContent, { type: 'base64' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet);

        if (!validateExcelData(jsonData)) {
          Alert.alert('Invalid File', 'Excel file must have exactly 37 rows and columns: date, history, onpromotion, is_holiday, transactions, store_nbr, item_nbr.');
          return;
        }

        const formData = new FormData();
        formData.append('file', {
          uri,
          name: name || 'upload.xlsx',
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        } as any);

        // Upload file to backend
        const uploadResponse = await forecastApi.post('/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        if (uploadResponse.data && uploadResponse.data.success) {
          // For the GCP backend, we need to make a separate request to get the forecast
          try {
            const forecastResponse = await gcpApi.getLatestForecast();
            const predictions = forecastResponse.predictions || [];
            
            // Save data to AsyncStorage for access by other screens
            await AsyncStorage.setItem('forecastData', JSON.stringify(predictions));
            
            Alert.alert('Success', 'File processed successfully! Please enter item and store details to generate your forecast.');
            setModalVisible(false);
            navigation.navigate('EnterDetailsScreen');
          } catch (forecastError) {
            console.error('Error fetching forecast:', forecastError);
            Alert.alert(
              'Upload Successful', 
              'File was uploaded successfully, but there was an issue retrieving the forecast. Please try again later.'
            );
          }
        } else {
          Alert.alert('Error', 'Failed to upload file. Please try again.');
        }
      } else {
        Alert.alert('Cancelled', 'No file selected.');
      }
    } catch (error: any) {
      console.error('Original upload error:', error);
      throw error;
    }
  };

  const downloadSample = async () => {
    try {
      // If GCP backend is available, try to download the template from there
      if (gcpHealthy) {
        await downloadTemplateFromCloud();
      } else {
        // Fallback to generating a sample locally
        await generateLocalSample();
      }
    } catch (error: any) {
      console.error('Download error:', error);
      Alert.alert('Error', 'Failed to download template file. Please try again.');
    }
  };
  
  const downloadTemplateFromCloud = async () => {
    try {
      console.log('Getting template from minimal API...');
      
      // Get the download URL with authentication
      const templateUrl = await gcpApi.getTemplateUrl();
      console.log('Template URL obtained');
      
      if (!templateUrl) {
        Alert.alert('Error', 'Failed to get template URL from API.');
        return;
      }
      
      // Download the file with authentication
      console.log('Downloading template file with authentication...');
      const fileUri = FileSystem.documentDirectory + 'sales_template.xlsx';
      
      // Check if file exists and delete if necessary
      const fileInfo = await FileSystem.getInfoAsync(fileUri);
      if (fileInfo.exists) {
        await FileSystem.deleteAsync(fileUri);
      }
      
      // Get auth token for download
      const token = await getAuthToken();
      
      const downloadResumable = FileSystem.createDownloadResumable(
        templateUrl,
        fileUri,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          }
        },
        (downloadProgress) => {
          const progress = downloadProgress.totalBytesWritten / downloadProgress.totalBytesExpectedToWrite;
          console.log(`Download progress: ${(progress * 100).toFixed(1)}%`);
        }
      );
      
      const downloadResult = await downloadResumable.downloadAsync();
      
      if (downloadResult && downloadResult.uri) {
        // Share the downloaded file
        console.log('Sharing template file...');
        if (await Sharing.isAvailableAsync()) {
          await Sharing.shareAsync(downloadResult.uri);
          Alert.alert('Success', 'Template downloaded successfully!');
        } else {
          Alert.alert('Error', 'Sharing is not available on this device');
        }
      } else {
        throw new Error('Download failed');
      }
    } catch (error) {
      console.error('Cloud template download error:', error);
      // Fall back to local template generation if Cloud fails
      Alert.alert(
        'Download Failed', 
        'Could not download the template from server. Would you like to generate a sample locally instead?',
        [
          {
            text: 'Cancel',
            style: 'cancel'
          },
          {
            text: 'Generate Sample',
            onPress: () => generateLocalSample()
          }
        ]
      );
    }
  };

  const generateLocalSample = async () => {
    try {
      console.log('Generating sample file locally...');
      const sampleData = Array.from({ length: 37 }, (_, i) => {
        const date = new Date(2023, 0, i + 1);
        return {
          date: date.toISOString().split('T')[0],
          history: i < 30 ? 100 + i * 5 : null,
          onpromotion: i % 2,
          is_holiday: i % 7 === 0 ? 1 : 0,
          transactions: 50 + i * 2,
          store_nbr: 1,
          item_nbr: 1,
        };
      });

      const ws = XLSX.utils.json_to_sheet(sampleData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'SampleData');
      const wbout = XLSX.write(wb, { type: 'base64', bookType: 'xlsx' });

      const uri = FileSystem.documentDirectory + 'sample_data.xlsx';
      await FileSystem.writeAsStringAsync(uri, wbout, {
        encoding: FileSystem.EncodingType.Base64,
      });

      await Sharing.shareAsync(uri);
      Alert.alert('Success', 'Sample file generated successfully!');
    } catch (error) {
      console.error('Local sample generation error:', error);
      throw error;
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#050A30', '#0B666A']} style={styles.gradientBackground}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Text style={styles.title}>Data Template</Text>
          <View style={styles.guideContainer}>
            <Text style={styles.guideTitle}>How to Prepare Your Data</Text>
            <View style={styles.backendIndicator}>
              <Text style={styles.backendText}>
                {gcpHealthy 
                  ? 'Using Minimal API for reliable predictions' 
                  : 'API not available (check connection)'}
              </Text>
            </View>
            <Text style={styles.guideText}>
              Upload an Excel file with exactly 37 rows and the following columns:
            </Text>
            <View style={styles.table}>
              <View style={styles.tableRow}>
                <Text style={styles.tableHeader}>Column</Text>
                <Text style={styles.tableHeader}>Description</Text>
              </View>
              <View style={styles.tableRow}>
                <Text style={styles.tableCell}>date</Text>
                <Text style={styles.tableCell}>Date in YYYY-MM-DD format (37 days)</Text>
              </View>
              <View style={styles.tableRow}>
                <Text style={styles.tableCell}>history</Text>
                <Text style={styles.tableCell}>Historical sales (30 days, null for last 7)</Text>
              </View>
              <View style={styles.tableRow}>
                <Text style={styles.tableCell}>onpromotion</Text>
                <Text style={styles.tableCell}>Items on promotion (0/1, 37 days)</Text>
              </View>
              <View style={styles.tableRow}>
                <Text style={styles.tableCell}>is_holiday</Text>
                <Text style={styles.tableCell}>Holiday indicator (0/1, 37 days)</Text>
              </View>
              <View style={styles.tableRow}>
                <Text style={styles.tableCell}>transactions</Text>
                <Text style={styles.tableCell}>Number of transactions (37 days)</Text>
              </View>
              <View style={styles.tableRow}>
                <Text style={styles.tableCell}>store_nbr</Text>
                <Text style={styles.tableCell}>Store ID (e.g., 1)</Text>
              </View>
              <View style={styles.tableRow}>
                <Text style={styles.tableCell}>item_nbr</Text>
                <Text style={styles.tableCell}>Item ID (e.g., 1)</Text>
              </View>
            </View>
            <TouchableOpacity style={styles.downloadButton} onPress={downloadSample}>
              <Feather name="download" size={20} color="#050A30" />
              <Text style={styles.downloadButtonText}>Download Sample</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.button} onPress={() => setModalVisible(true)}>
              <Text style={styles.buttonText}>Get Started</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </LinearGradient>

      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <LinearGradient colors={['#050A30', '#0B666A']} style={styles.modalGradient}>
            <Text style={styles.modalTitle}>Upload Template</Text>
            <Text style={styles.modalText}>
              Select an Excel file with your data to generate a forecast.
            </Text>
            <TouchableOpacity style={styles.uploadButton} onPress={uploadFile} disabled={uploading}>
              {uploading ? (
                <ActivityIndicator color="#050A30" size="small" />
              ) : (
                <Text style={styles.uploadButtonText}>Select File</Text>
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          </LinearGradient>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradientBackground: {
    flex: 1,
  },
  scrollContent: {
    alignItems: 'center',
    padding: 20,
    paddingBottom: 40,
  },
  backendIndicator: {
    backgroundColor: '#97FEED22',
    padding: 8,
    borderRadius: 8,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#97FEED44',
  },
  backendText: {
    color: '#97FEED',
    fontSize: 14,
    textAlign: 'center',
  },
  title: {
    color: '#97FEED',
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 20,
    textShadowColor: '#97FEED',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 12,
  },
  guideContainer: {
    width: '100%',
    backgroundColor: '#050A30AA',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#97FEED33',
  },
  guideTitle: {
    color: '#97FEED',
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 10,
  },
  guideText: {
    color: '#97FEED',
    fontSize: 16,
    marginBottom: 15,
  },
  table: {
    width: '100%',
    borderWidth: 1,
    borderColor: '#97FEED66',
    borderRadius: 5,
    overflow: 'hidden',
    marginBottom: 15,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#97FEED66',
  },
  tableHeader: {
    flex: 1,
    padding: 10,
    backgroundColor: '#97FEED33',
    color: '#97FEED',
    fontWeight: '600',
    textAlign: 'center',
  },
  tableCell: {
    flex: 1,
    padding: 10,
    color: '#97FEED',
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#050A30',
    fontSize: 18,
    fontWeight: '600',
  },
  downloadButton: {
    backgroundColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 10,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: 10,
  },
  downloadButtonText: {
    color: '#050A30',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalGradient: {
    width: '90%',
    borderRadius: 15,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#97FEED33',
  },
  modalTitle: {
    color: '#97FEED',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  modalText: {
    color: '#97FEED',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  uploadButton: {
    backgroundColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    width: '60%',
    marginBottom: 15,
  },
  uploadButtonText: {
    color: '#050A30',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelButton: {
    backgroundColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    width: '60%',
  },
  cancelButtonText: {
    color: '#050A30',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default TemplateScreen;
