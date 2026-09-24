import React from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import i18n from './i18n';
import './index.css';
class Boundary extends React.Component {
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<main className="fatal"><h1>{i18n.t('fatal')}</h1><button onClick={()=>location.reload()}>{i18n.t('reload')}</button></main>:this.props.children}
}
createRoot(document.getElementById('root')).render(<React.StrictMode><Boundary><App/></Boundary></React.StrictMode>);
if(import.meta.env.PROD && 'serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
