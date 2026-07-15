import React from 'react';
import {createRoot} from 'react-dom/client';
import './index.css';
import 'flexlayout-react/style/dark.css'
import 'react-contexify/dist/ReactContexify.min.css';
import App from './Components/App/App';
import {AppProvider} from "./Context/AppContext";
import {LayoutProvider} from "./Layout/LayoutContext";

// React 18 root API (replaces ReactDOM.render).
const root = createRoot(document.getElementById('root'));
root.render(
    <LayoutProvider>
        <AppProvider>
            <App/>
        </AppProvider>
    </LayoutProvider>
);
