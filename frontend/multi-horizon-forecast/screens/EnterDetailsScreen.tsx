import * as React from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';

type RootStackParamList = {
  HomeScreen: undefined;
  ForecastScreen: { itemName: string; storeName: string };
  SavedForecastsScreen: undefined;
};

type NavigationProp = NativeStackNavigationProp<RootStackParamList, 'ForecastScreen'>;

const EnterDetailsScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const [itemName, setItemName] = React.useState<string>('');
  const [storeName, setStoreName] = React.useState<string>('');
  
  // Clear any existing forecast data when this screen mounts
  React.useEffect(() => {
    const clearExistingData = async () => {
      try {
        // Remove existing forecast data to ensure we get a fresh forecast
        // with the new store and item parameters
        await AsyncStorage.removeItem('forecastData');
        console.log('Cleared existing forecast data for fresh start');
      } catch (error) {
        console.error('Error clearing forecast data:', error);
      }
    };
    
    clearExistingData();
  }, []);

  const handleProceed = () => {
    if (!itemName.trim()) {
      Alert.alert('Error', 'Please enter an item name');
      return;
    }
    if (!storeName.trim()) {
      Alert.alert('Error', 'Please enter a store name');
      return;
    }

    // Navigate to ForecastScreen with the entered details
    navigation.navigate('ForecastScreen', {
      itemName: itemName.trim(),
      storeName: storeName.trim()
    });
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#050A30', '#0B666A']} style={styles.gradientBackground}>
        <View style={styles.content}>
          <Text style={styles.title}>Enter Forecast Details</Text>
          <Text style={styles.subtitle}>Please provide the item and store information for your forecast</Text>
          
          <View style={styles.inputContainer}>
            <Text style={styles.label}>Item Name</Text>
            <TextInput
              style={styles.input}
              value={itemName}
              onChangeText={setItemName}
              placeholder="e.g., Milk 1L, Bread, Eggs"
              placeholderTextColor="#97FEED66"
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Store Name</Text>
            <TextInput
              style={styles.input}
              value={storeName}
              onChangeText={setStoreName}
              placeholder="e.g., Main Store, Downtown Branch"
              placeholderTextColor="#97FEED66"
            />
          </View>

          <View style={styles.buttonContainer}>
            <TouchableOpacity 
              style={styles.backButton} 
              onPress={() => navigation.navigate('HomeScreen')}
            >
              <Text style={styles.backButtonText}>Back</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.proceedButton} 
              onPress={handleProceed}
            >
              <Text style={styles.proceedButtonText}>Generate Forecast</Text>
            </TouchableOpacity>
          </View>
        </View>
      </LinearGradient>
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
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    color: '#97FEED',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
    textShadowColor: '#97FEED',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 12,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginTop: 20,
  },
  backButton: {
    backgroundColor: '#050A30',
    borderWidth: 1,
    borderColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 100,
  },
  backButtonText: {
    color: '#97FEED',
    fontSize: 16,
    fontWeight: '600',
  },
  subtitle: {
    color: '#97FEED',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 20,
  },
  inputContainer: {
    width: '100%',
    marginBottom: 25,
  },
  proceedButton: {
    backgroundColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 160,
  },
  proceedButtonText: {
    color: '#050A30',
    fontSize: 16,
    fontWeight: 'bold',
  },
  label: {
    color: '#97FEED',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#050A30AA',
    color: '#97FEED',
    borderWidth: 2,
    borderColor: '#97FEED66',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    width: '100%',
  },
});

export default EnterDetailsScreen;
