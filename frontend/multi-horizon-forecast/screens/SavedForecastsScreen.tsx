import * as React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';

type RootStackParamList = {
  ForecastScreen: { itemName: string; storeName: string };
  InsightsScreen: {
    forecast: { p10: number[]; p50: number[]; p90: number[] };
    store_name: string;
    item_name: string;
  };
};

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

interface SavedForecast {
  key: string;
  store_name: string;
  item_name: string;
  forecast_days: number;
  created_at: string;
  forecast: { p10: number[]; p50: number[]; p90: number[] };
}

const SavedForecastsScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const [savedForecasts, setSavedForecasts] = React.useState<SavedForecast[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);

  React.useEffect(() => {
    loadSavedForecasts();
  }, []);

  const loadSavedForecasts = async () => {
    try {
      const existingSaves = await AsyncStorage.getItem('saved_forecasts');
      const savedList = existingSaves ? JSON.parse(existingSaves) : [];
      
      // Load the full forecast data for each saved item
      const forecastsWithData = await Promise.all(
        savedList.map(async (save: any) => {
          try {
            const fullData = await AsyncStorage.getItem(save.key);
            if (fullData) {
              const parsedData = JSON.parse(fullData);
              // Make sure to use metadata values if available
              return {
                ...save,
                store_name: parsedData.metadata?.store_name || save.store_name,
                item_name: parsedData.metadata?.item_name || save.item_name,
                forecast: parsedData.forecast
              };
            }
            return save;
          } catch (error) {
            console.error('Error loading forecast data:', error);
            return save;
          }
        })
      );
      
      setSavedForecasts(forecastsWithData);
    } catch (error) {
      console.error('Error loading saved forecasts:', error);
      Alert.alert('Error', 'Failed to load saved forecasts.');
    } finally {
      setLoading(false);
    }
  };

  const deleteForecast = async (forecastKey: string) => {
    Alert.alert(
      'Delete Forecast',
      'Are you sure you want to delete this forecast?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              // Remove from storage
              await AsyncStorage.removeItem(forecastKey);
              
              // Update the saved forecasts list
              const existingSaves = await AsyncStorage.getItem('saved_forecasts');
              const savedList = existingSaves ? JSON.parse(existingSaves) : [];
              const updatedList = savedList.filter((save: any) => save.key !== forecastKey);
              await AsyncStorage.setItem('saved_forecasts', JSON.stringify(updatedList));
              
              // Reload the list
              loadSavedForecasts();
            } catch (error) {
              console.error('Error deleting forecast:', error);
              Alert.alert('Error', 'Failed to delete forecast.');
            }
          }
        }
      ]
    );
  };

  const viewForecastDetails = (forecast: SavedForecast) => {
    if (forecast.forecast) {
      // Log the values to verify they're correct before navigating
      console.log('Opening insights with store name:', forecast.store_name);
      console.log('Opening insights with item name:', forecast.item_name);
      
      navigation.navigate('InsightsScreen', {
        forecast: forecast.forecast,
        store_name: forecast.store_name || 'Unknown Store',
        item_name: forecast.item_name || 'Unknown Item',
      });
    } else {
      Alert.alert('Error', 'Forecast data not available.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateAverage = (forecast: { p10: number[]; p50: number[]; p90: number[] }) => {
    if (!forecast || !forecast.p50 || forecast.p50.length === 0) return 0;
    const sum = forecast.p50.reduce((acc, val) => acc + val, 0);
    return (sum / forecast.p50.length).toFixed(1);
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <LinearGradient colors={['#050A30', '#0B666A']} style={styles.gradientBackground}>
          <View style={styles.centerContent}>
            <Text style={styles.loadingText}>Loading saved forecasts...</Text>
          </View>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#050A30', '#0B666A']} style={styles.gradientBackground}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Text style={styles.title}>Saved Forecasts</Text>
          
          {savedForecasts.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No saved forecasts found</Text>
              <Text style={styles.emptySubtext}>Create and save forecasts to view them here</Text>
            </View>
          ) : (
            savedForecasts.map((forecast, index) => (
              <View key={index} style={styles.forecastCard}>
                <View style={styles.forecastHeader}>
                  <Text style={styles.forecastTitle}>{forecast.item_name}</Text>
                  <Text style={styles.forecastStore}>{forecast.store_name}</Text>
                </View>
                
                <View style={styles.forecastDetails}>
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Forecast Days:</Text>
                    <Text style={styles.detailValue}>{forecast.forecast_days}</Text>
                  </View>
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Average Daily Sales:</Text>
                    <Text style={styles.detailValue}>{calculateAverage(forecast.forecast)} units</Text>
                  </View>
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Created:</Text>
                    <Text style={styles.detailValue}>{formatDate(forecast.created_at)}</Text>
                  </View>
                </View>

                <View style={styles.forecastActions}>
                  <TouchableOpacity 
                    style={styles.viewButton} 
                    onPress={() => viewForecastDetails(forecast)}
                  >
                    <Text style={styles.viewButtonText}>View Details</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.deleteButton} 
                    onPress={() => deleteForecast(forecast.key)}
                  >
                    <Text style={styles.deleteButtonText}>Delete</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}
        </ScrollView>
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
  scrollContent: {
    padding: 20,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    color: '#97FEED',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    textShadowColor: '#97FEED',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 12,
  },
  loadingText: {
    color: '#97FEED',
    fontSize: 18,
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 50,
  },
  emptyText: {
    color: '#97FEED',
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 10,
  },
  emptySubtext: {
    color: '#97FEED',
    fontSize: 16,
    textAlign: 'center',
  },
  forecastCard: {
    backgroundColor: '#050A30AA',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#97FEED33',
  },
  forecastHeader: {
    marginBottom: 15,
  },
  forecastTitle: {
    color: '#97FEED',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  forecastStore: {
    color: '#97FEED',
    fontSize: 16,
    opacity: 0.8,
  },
  forecastDetails: {
    marginBottom: 15,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    color: '#97FEED',
    fontSize: 14,
    opacity: 0.8,
  },
  detailValue: {
    color: '#97FEED',
    fontSize: 14,
    fontWeight: '600',
  },
  forecastActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  viewButton: {
    backgroundColor: '#97FEED',
    padding: 10,
    borderRadius: 20,
    flex: 1,
    marginRight: 10,
    alignItems: 'center',
  },
  viewButtonText: {
    color: '#050A30',
    fontSize: 14,
    fontWeight: '600',
  },
  deleteButton: {
    backgroundColor: '#FF4444',
    padding: 10,
    borderRadius: 20,
    flex: 1,
    marginLeft: 10,
    alignItems: 'center',
  },
  deleteButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default SavedForecastsScreen;
