import * as React from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { useRoute, RouteProp, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { forecastApi } from '../api/api';
import NavigationGuard from '../components/NavigationGuard';

// Navigation types
type RootStackParamList = {
  LoginScreen: undefined;
  ForecastScreen: undefined;
  HomeScreen: undefined;
  InsightsScreen: {
    forecast?: { p10: number[]; p50: number[]; p90: number[] };
    store_name?: string;
    item_name?: string;
  };
};

// Prediction type
interface Prediction {
  item_name: string;
  store_name: string;
  forecast: { p10: number[]; p50: number[]; p90: number[] };
  suggestions: { type: string; message: string; confidence: number }[];
  timestamp: string;
  filename: string;
}

// ChartData type for react-native-chart-kit
interface ChartData {
  labels: string[];
  datasets: { data: number[] }[];
}

type InsightsRouteProp = RouteProp<RootStackParamList, 'InsightsScreen'>;
type NavigationProp = NativeStackNavigationProp<RootStackParamList, 'InsightsScreen'>;

const InsightsScreen: React.FC = () => {
  const route = useRoute<InsightsRouteProp>();
  const navigation = useNavigation<NavigationProp>();
  const [predictions, setPredictions] = React.useState<Prediction[]>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [userStoreName, setUserStoreName] = React.useState<string>('Unknown Store');
  const [selectedItemName, setSelectedItemName] = React.useState<string>('Milk 1L');
  const [fallbackForecast, setFallbackForecast] = React.useState<{
    p10: number[];
    p50: number[];
    p90: number[];
  }>({ p10: [], p50: [], p90: [] });

  React.useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        // Skip API calls that cause "Not Found" errors
        // Just use route params or fallback data
        
        // If no route params (e.g., from Home Page), use fallback data
        if (!route.params?.forecast || !route.params?.store_name || !route.params?.item_name) {
          // Try to get saved forecasts from AsyncStorage instead of API
          try {
            const existingSaves = await AsyncStorage.getItem('saved_forecasts');
            const savedList = existingSaves ? JSON.parse(existingSaves) : [];
            
            if (savedList.length > 0) {
              // Select the most recent prediction
              const latestSave = savedList[0]; // Already sorted by most recent
              const fullData = await AsyncStorage.getItem(latestSave.key);
              
              if (fullData) {
                const parsedData = JSON.parse(fullData);
                setSelectedItemName(latestSave.item_name);
                setFallbackForecast(parsedData.forecast);
                setUserStoreName(latestSave.store_name);
                
                // Load all saved forecasts for averages calculation
                const allForecasts = await Promise.all(
                  savedList.map(async (save: any) => {
                    try {
                      const data = await AsyncStorage.getItem(save.key);
                      if (data) {
                        const parsed = JSON.parse(data);
                        return {
                          item_name: save.item_name,
                          store_name: save.store_name,
                          forecast: parsed.forecast,
                          timestamp: save.created_at
                        };
                      }
                    } catch (error) {
                      console.error('Error loading saved forecast:', error);
                    }
                    return null;
                  })
                );
                
                const validForecasts = allForecasts.filter(f => f !== null);
                setPredictions(validForecasts);
              }
            } else {
              // No saved forecasts available
              Alert.alert(
                'No Predictions',
                'No forecast data available. Please generate a forecast first.',
                [{ text: 'OK', onPress: () => navigation.navigate('ForecastScreen') }]
              );
              setFallbackForecast({ p10: Array(7).fill(0), p50: Array(7).fill(50), p90: Array(7).fill(100) });
            }
          } catch (storageError) {
            console.error('Error loading from storage:', storageError);
            setFallbackForecast({ p10: Array(7).fill(0), p50: Array(7).fill(50), p90: Array(7).fill(100) });
          }
        }
      } catch (error: any) {
        console.error('Initialization error:', error);
        // Don't show API error alerts, just use fallback data
        setFallbackForecast({ p10: Array(7).fill(0), p50: Array(7).fill(50), p90: Array(7).fill(100) });
      } finally {
        setLoading(false);
      }
    };
    initializeData();
  }, [navigation, route.params]);

  const effectiveStoreName = route.params?.store_name || userStoreName;
  const effectiveItemName = route.params?.item_name || selectedItemName;
  const effectiveForecast = route.params?.forecast || fallbackForecast;

  const chartData = {
    p10: effectiveForecast.p10.length ? effectiveForecast.p10 : Array(7).fill(0),
    p50: effectiveForecast.p50.length ? effectiveForecast.p50 : Array(7).fill(50),
    p90: effectiveForecast.p90.length ? effectiveForecast.p90 : Array(7).fill(100),
  };

  const storePredictions = predictions.filter((p) => p.store_name === effectiveStoreName);

  const itemAverages = storePredictions.reduce((acc, pred) => {
    const avgP50 =
      pred.forecast.p50.reduce((sum: number, val: number) => sum + val, 0) / pred.forecast.p50.length;
    acc[pred.item_name] = avgP50;
    return acc;
  }, {} as Record<string, number>);

  const barChartData: ChartData = {
    labels: Object.keys(itemAverages).length ? Object.keys(itemAverages) : ['No Items'],
    datasets: [
      {
        data: Object.keys(itemAverages).length
          ? Object.values(itemAverages).map((value) => Number(value))
          : [0],
      },
    ],
  };

  const generateInsights = () => {
    const insights = [];

    const avgP50 = chartData.p50.reduce((sum, val) => sum + val, 0) / chartData.p50.length;
    const minP50 = Math.min(...chartData.p50);
    const maxP50 = Math.max(...chartData.p50);
    const avgP10 = chartData.p10.reduce((sum, val) => sum + val, 0) / chartData.p10.length;
    const avgP90 = chartData.p90.reduce((sum, val) => sum + val, 0) / chartData.p90.length;
    
    // Stock adjustment based on real forecast data
    const safetyStock = Math.ceil(avgP90 * 1.1); // 10% above P90 average
    insights.push({
      type: 'Stock Adjustment',
      message: `Based on forecasted average of ${avgP50.toFixed(1)} units/day for ${effectiveItemName}, maintain stock levels of at least ${safetyStock} units to handle demand uncertainty (P90: ${avgP90.toFixed(1)}).`,
    });

    // Volatility analysis based on actual data spread
    const volatility = avgP90 - avgP10;
    const volatilityRatio = volatility / avgP50;
    if (volatilityRatio > 1.0) {
      insights.push({
        type: 'High Volatility Alert',
        message: `${effectiveItemName} shows high demand volatility (range: ${volatility.toFixed(1)} units). Consider flexible inventory strategies and monitor daily demand closely.`,
      });
    }

    // Peak demand analysis
    const peakDays = chartData.p50.filter(val => val > avgP50 * 1.2).length;
    if (peakDays > 0) {
      insights.push({
        type: 'Peak Demand Strategy',
        message: `${peakDays} day(s) show elevated demand (>20% above average). Peak demand reaches ${maxP50.toFixed(1)} units. Plan promotional activities and staff allocation accordingly.`,
      });
    }

    // Trend analysis based on actual forecast progression
    const firstHalf = chartData.p50.slice(0, Math.ceil(chartData.p50.length / 2));
    const secondHalf = chartData.p50.slice(Math.ceil(chartData.p50.length / 2));
    const firstHalfAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondHalfAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
    const trendChange = ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100;
    
    if (Math.abs(trendChange) > 5) {
      const trendDirection = trendChange > 0 ? 'increasing' : 'decreasing';
      insights.push({
        type: 'Demand Trend',
        message: `${effectiveItemName} demand is ${trendDirection} by ${Math.abs(trendChange).toFixed(1)}% over the forecast period. Adjust procurement and marketing strategies accordingly.`,
      });
    }

    // Risk assessment based on confidence intervals
    const riskLevel = (avgP90 - avgP10) / avgP50;
    if (riskLevel > 0.8) {
      insights.push({
        type: 'Risk Management',
        message: `High uncertainty detected for ${effectiveItemName} (confidence interval: ${(riskLevel * 100).toFixed(0)}% of mean). Implement dynamic pricing and flexible supply chain strategies.`,
      });
    }

    // Low demand warning
    if (minP50 < avgP50 * 0.7) {
      insights.push({
        type: 'Low Demand Alert',
        message: `Minimum forecasted demand for ${effectiveItemName} is ${minP50.toFixed(1)} units (${((minP50/avgP50) * 100).toFixed(0)}% of average). Consider promotional strategies for low-demand periods.`,
      });
    }

    // Multi-item comparison (only if we have multiple items)
    if (Object.keys(itemAverages).length > 1) {
      const sortedItems = Object.entries(itemAverages).sort((a, b) => b[1] - a[1]);
      const topItem = sortedItems[0];
      const currentItemRank = sortedItems.findIndex(([name]) => name === effectiveItemName) + 1;
      
      insights.push({
        type: 'Performance Comparison',
        message: `${effectiveItemName} ranks #${currentItemRank} out of ${sortedItems.length} items in ${effectiveStoreName}. Top performer: ${topItem[0]} (${topItem[1].toFixed(1)} units/day). ${currentItemRank === 1 ? 'Maintain leadership position.' : 'Consider strategies to improve performance.'}`,
      });
    }

    return insights;
  };

  const insights = generateInsights();

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#050A30', '#0B666A']} style={styles.gradientBackground}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Text style={styles.title}>
            {effectiveStoreName} - {effectiveItemName}
          </Text>
          <Text style={styles.subtitle}>Sales Forecast for {effectiveItemName} (Next 7 Days)</Text>
          <Text style={styles.chartDescription}>
            Shows predicted sales units: p50 (median, magenta), p10/p90 (low/high bounds, green).
          </Text>
          <LineChart
            data={{
              labels: ['1', '2', '3', '4', '5', '6', '7'],
              datasets: [
                {
                  data: chartData.p10,
                  color: () => '#00FF00',
                  strokeWidth: 1,
                },
                {
                  data: chartData.p50,
                  color: () => '#FF00FF',
                  strokeWidth: 2,
                },
                {
                  data: chartData.p90,
                  color: () => '#00FF00',
                  strokeWidth: 1,
                },
              ],
            }}
            width={Dimensions.get('window').width - 40}
            height={220}
            chartConfig={{
              backgroundGradientFrom: '#050A30',
              backgroundGradientTo: '#0B666A',
              decimalPlaces: 0,
              color: () => '#97FEED',
              labelColor: () => '#97FEED',
              style: {
                borderRadius: 16,
                paddingLeft: 15, // Add padding to prevent Y-axis cutoff
              },
              propsForDots: {
                r: '4',
                strokeWidth: '2',
                stroke: '#97FEED',
              },
              propsForBackgroundLines: {
                strokeDasharray: '',
                strokeWidth: 0.5,
              },
              formatYLabel: (value) => Math.round(Number(value)).toString(),
            }}
            bezier // Smoother curve
            style={styles.chart}
            verticalLabelRotation={0} // Horizontal labels
            fromZero={true} // Start Y-axis from zero
            withInnerLines={true} // Show grid lines
            withOuterLines={true} // Show outer lines
          />
          <Text style={styles.subtitle}>Smart Forecast Analysis</Text>
          <Text style={styles.chartDescription}>
            Actionable recommendations based on forecast data for {effectiveItemName}.
          </Text>
          <View style={styles.insightsContainer}>
            {insights.length ? (
              insights.map((insight, index) => (
                <View key={index} style={styles.insightItem}>
                  <Text style={styles.insightTitle}>{insight.type}</Text>
                  <Text style={styles.insightText}>{insight.message}</Text>
                </View>
              ))
            ) : (
              <Text style={styles.guideText}>No insights available.</Text>
            )}
          </View>
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
    alignItems: 'center',
  },
  title: {
    color: '#97FEED',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 20,
    textShadowColor: '#97FEED',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 8,
  },
  subtitle: {
    color: '#97FEED',
    fontSize: 20,
    fontWeight: '600',
    marginTop: 20,
    marginBottom: 5,
  },
  chartDescription: {
    color: '#97FEED',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 10,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  guideText: {
    color: '#97FEED',
    fontSize: 16,
    textAlign: 'center',
    marginVertical: 10,
  },
  insightsContainer: {
    width: '100%',
    marginTop: 20,
    marginBottom: 40,
  },
  insightItem: {
    backgroundColor: '#062743',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
  },
  insightTitle: {
    color: '#97FEED',
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 4,
  },
  insightText: {
    color: '#97FEED',
    fontSize: 14,
  },
});

// Wrap InsightsScreen with NavigationGuard
const InsightsScreenWithGuard: React.FC = () => {
  return (
    <NavigationGuard>
      <InsightsScreen />
    </NavigationGuard>
  );
};

export default InsightsScreenWithGuard;