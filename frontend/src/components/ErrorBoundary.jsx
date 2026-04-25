import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || 'Unknown React error' }
  }

  componentDidCatch(error, info) {
    console.error('UI crash caught by ErrorBoundary:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ fontFamily: 'system-ui, sans-serif', padding: '24px' }}>
          <h1 style={{ marginBottom: '10px' }}>Frontend failed to render</h1>
          <p style={{ marginBottom: '6px' }}>
            Open browser DevTools Console and share the error if this persists.
          </p>
          <pre style={{ background: '#f4f4f5', padding: '12px', borderRadius: '8px', overflowX: 'auto' }}>
            {this.state.message}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}
