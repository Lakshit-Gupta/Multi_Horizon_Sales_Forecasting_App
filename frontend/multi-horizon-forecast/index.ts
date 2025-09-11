// Must be the first import
import 'react-native-gesture-handler';
import { enableScreens } from 'react-native-screens';
import { registerRootComponent } from 'expo';
import { LogBox } from 'react-native';

// Enable screens for better navigation performance
enableScreens();

// Ignore specific warnings that might be related to third-party libraries
LogBox.ignoreLogs([
  'ViewPropTypes will be removed',
  'AsyncStorage has been extracted from react-native',
  'Possible Unhandled Promise Rejection',
  "[react-native-gesture-handler] Seems like you're using an old API"
]);

import App from './App';

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);
