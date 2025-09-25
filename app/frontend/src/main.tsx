import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
// import App from './App.simple.tsx'
// import App from './App.router.tsx'
// import App from './App.antd.tsx'
// import App from './App.query.tsx'
// import App from './App.mainlayout.tsx'
// import App from './App.contenttest.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
