// App.tsx
import * as React from 'react';
import { View, Text } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import HomeScreen from './screens/HomeScreen';
import TemplateScreen from './screens/TemplateScreen';
import ForecastScreen from './screens/ForecastScreen';
import InsightsScreen from './screens/InsightsScreen';
import LoginScreen from './screens/LoginScreen';
import EnterDetailsScreen from './screens/EnterDetailsScreen';
import SavedForecastsScreen from './screens/SavedForecastsScreen';
import * as WebBrowser from 'expo-web-browser';
import { onAuthChange } from './services/auth';
import { User } from 'firebase/auth';
import { DataProvider, useDataContext } from './contexts/DataContext';

// Important: Call this before anything else to properly complete auth sessions
WebBrowser.maybeCompleteAuthSession();

type RootStackParamList = {
  LoginScreen: undefined;
  RegisterScreen: undefined;
  HomeScreen: undefined;
  TemplateScreen: undefined;
  EnterDetailsScreen: undefined;
  ForecastScreen: { itemName?: string; storeName?: string };
  InsightsScreen: undefined;
  SavedForecastsScreen: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const App: React.FC = () => {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  
  React.useEffect(() => {
    const unsubscribe = onAuthChange((currentUser: User | null) => {
      console.log("Auth state changed, user:", currentUser?.uid || "No user");
      setUser(currentUser);
      setIsLoading(false);
    });
    
    // Clean up subscription
    return unsubscribe;
  }, []);
  
  if (isLoading) {
    // Return a loading screen if still checking token
    return (
      <View style={{flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#050A30'}}>
        <Text style={{color: '#97FEED', fontSize: 20}}>Loading...</Text>
      </View>
    );
  }

  return (
    <DataProvider>
      <NavigationContainer>
        {!user ? (
          <Stack.Navigator initialRouteName="LoginScreen" screenOptions={{ headerShown: false }}>
            <Stack.Screen name="LoginScreen" component={LoginScreen} />
          </Stack.Navigator>
        ) : (
          <Stack.Navigator initialRouteName="HomeScreen" screenOptions={{ headerShown: false }}>
            <Stack.Screen name="HomeScreen" component={HomeScreen} />
            <Stack.Screen name="TemplateScreen" component={TemplateScreen} />
            <Stack.Screen name="EnterDetailsScreen" component={EnterDetailsScreen} />
            <Stack.Screen name="ForecastScreen" component={ForecastScreen} />
            <Stack.Screen name="InsightsScreen" component={InsightsScreen} />
            <Stack.Screen name="SavedForecastsScreen" component={SavedForecastsScreen} />
          </Stack.Navigator>
        )}
      </NavigationContainer>
    </DataProvider>
  );
};

export default App;