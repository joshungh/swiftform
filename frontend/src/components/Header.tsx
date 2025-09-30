import React from 'react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import {
  Home,
  CloudUpload,
  History,
  ModelTraining,
  Description,
  Menu,
  Close
} from '@mui/icons-material'
import { useState } from 'react'

const Header: React.FC = () => {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Upload', href: '/upload', icon: CloudUpload },
    { name: 'History', href: '/history', icon: History },
  ]

  const isActive = (path: string) => location.pathname === path

  return (
    <nav className="bg-primary-600 shadow-lg">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <RouterLink to="/" className="flex items-center space-x-3">
              <Description className="h-8 w-8 text-white" />
              <span className="text-xl font-semibold text-white">SwiftForm AI</span>
            </RouterLink>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden sm:flex sm:items-center sm:space-x-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)
              return (
                <RouterLink
                  key={item.name}
                  to={item.href}
                  className={`
                    inline-flex items-center px-4 py-2 text-sm font-medium rounded-md
                    transition-colors duration-200
                    ${active
                      ? 'bg-primary-700 text-white'
                      : 'text-primary-100 hover:bg-primary-700 hover:text-white'
                    }
                  `}
                >
                  <Icon className="mr-2 h-5 w-5" />
                  {item.name}
                </RouterLink>
              )
            })}

            {/* Training Dashboard Button */}
            <button
              onClick={() => window.open('http://localhost:8000/training-dashboard', '_blank')}
              className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md
                text-primary-100 hover:bg-primary-700 hover:text-white
                transition-colors duration-200"
            >
              <ModelTraining className="mr-2 h-5 w-5" />
              Training
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center sm:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-primary-100
                hover:bg-primary-700 hover:text-white focus:outline-none focus:ring-2
                focus:ring-inset focus:ring-white"
            >
              {mobileMenuOpen ? (
                <Close className="block h-6 w-6" />
              ) : (
                <Menu className="block h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {mobileMenuOpen && (
        <div className="sm:hidden bg-primary-700">
          <div className="space-y-1 px-2 pb-3 pt-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)
              return (
                <RouterLink
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`
                    block px-3 py-2 rounded-md text-base font-medium
                    ${active
                      ? 'bg-primary-800 text-white'
                      : 'text-primary-100 hover:bg-primary-800 hover:text-white'
                    }
                  `}
                >
                  <div className="flex items-center">
                    <Icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </div>
                </RouterLink>
              )
            })}

            {/* Training Dashboard Mobile */}
            <button
              onClick={() => {
                window.open('http://localhost:8000/training-dashboard', '_blank')
                setMobileMenuOpen(false)
              }}
              className="w-full text-left block px-3 py-2 rounded-md text-base font-medium
                text-primary-100 hover:bg-primary-800 hover:text-white"
            >
              <div className="flex items-center">
                <ModelTraining className="mr-3 h-5 w-5" />
                Training Dashboard
              </div>
            </button>
          </div>
        </div>
      )}
    </nav>
  )
}

export default Header