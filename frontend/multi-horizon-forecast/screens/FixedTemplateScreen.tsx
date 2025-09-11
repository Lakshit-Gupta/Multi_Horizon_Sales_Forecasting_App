// This is the fixed version of the TemplateScreen.tsx file
// Copy the content of this file into your TemplateScreen.tsx file to fix the syntax errors

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
import { forecastApi, gcpApi } from '../api/api'; // Import APIs

const TemplateScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const [modalVisible, setModalVisible] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [useAWSBackend, setUseAWSBackend] = React.useState(true); // Default to AWS
  const [awsHealthy, setAwsHealthy] = React.useState(false);

  // Check AWS health on component mount
  React.useEffect(() => {
    checkAWSHealth();
  }, []);

  const checkAWSHealth = async () => {
    try {
      // Since we're not using AWS anymore, we'll just set awsHealthy to false
      setAwsHealthy(false);
      setUseAWSBackend(false);
    } catch (error) {
      console.log('AWS backend not available, falling back to original backend');
      setAwsHealthy(false);
      setUseAWSBackend(false);
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
      // Always use GCP method now
      await uploadFileAWS(); // We'll keep the function name for now
    } catch (error: any) {
      console.error('Upload failed:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to upload file. Please ensure you are logged in and try again.');
    } finally {
      setUploading(false);
    }
  };

  const uploadFileAWS = async () => {
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
        
        // Step 3: Upload directly to GCP
        console.log('� Uploading file to GCP Storage...');
        const fileName = `upload_${new Date().toISOString().replace(/[-:.]/g, '')}.xlsx`;
        
        // Use GCP API to upload
        const response = await gcpApi.uploadFile(
          uri, 
          fileName,
          mimeType || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        );
        
        // Step 4: Process the uploaded file and get predictions
        console.log('Processing file and generating predictions...');
        const predictions = response.predictions;
        
        // Check for both object with predictions property and direct array format
        if (!predictions || (!predictions.predictions && !Array.isArray(predictions))) {
          Alert.alert('Error', 'Failed to generate predictions from the uploaded file.');
          return;
        }
        
        // Store predictions for use in ForecastScreen
        const forecastData = Array.isArray(predictions) ? predictions : predictions.predictions;
        await AsyncStorage.setItem('forecastData', JSON.stringify(forecastData));
        
        Alert.alert(
          'Success', 
          'File processed successfully! View your forecast now.',
          [{ text: 'OK', onPress: () => {
            setModalVisible(false);
            navigation.navigate('ForecastScreen');
          }}]
        );
      } else {
        console.log('File selection cancelled or failed');
        Alert.alert('Cancelled', 'No file selected.');
      }
    } catch (error: any) {
      console.error('AWS upload error:', error);
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

        const response = await forecastApi.post('/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        Alert.alert('Success', `File uploaded successfully! Rows: ${response.data.row_count}`);
        setModalVisible(false);
        navigation.navigate('ForecastScreen');
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
      // Always use GCP backend now
      await downloadTemplateFromAWS(); // We'll keep the function name for now
    } catch (error: any) {
      console.error('Download error:', error);
      Alert.alert('Error', 'Failed to download template file. Please try again.');
    }
  };
  
  const downloadTemplateFromAWS = async () => {
    try {
      console.log('Getting template from GCP...');
      const templateUrl = await gcpApi.getTemplateUrl();
      
      if (!templateUrl) {
        Alert.alert('Error', 'Failed to get template URL from GCP.');
        return;
      }
      
      // Download the file
      console.log('Downloading template file...');
      const downloadResumable = FileSystem.createDownloadResumable(
        templateUrl,
        FileSystem.documentDirectory + 'sales_template.xlsx',
        {},
        (downloadProgress) => {
          const progress = downloadProgress.totalBytesWritten / downloadProgress.totalBytesExpectedToWrite;
          console.log(`Download progress: ${progress * 100}%`);
        }
      );
      
      const downloadResult = await downloadResumable.downloadAsync();
      
      if (downloadResult) {
        // Share the downloaded file
        console.log('Sharing template file...');
        await Sharing.shareAsync(downloadResult.uri);
        Alert.alert('Success', 'Template downloaded successfully!');
      } else {
        throw new Error('Download failed');
      }
    } catch (error) {
      console.error('AWS template download error:', error);
      throw error;
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
                Using Google Cloud Storage for files
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
