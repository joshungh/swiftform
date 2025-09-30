import React from 'react'
import { useNavigate } from 'react-router-dom'
import { CloudUpload, Description, AutoAwesome, Download } from '@mui/icons-material'

const HomePage: React.FC = () => {
  const navigate = useNavigate()

  const features = [
    {
      icon: Description,
      title: 'Upload Document',
      description: 'PDF, Word, or Excel files',
      color: 'text-blue-600'
    },
    {
      icon: AutoAwesome,
      title: 'Process with AI',
      description: 'Extract form structure',
      color: 'text-purple-600'
    },
    {
      icon: Download,
      title: 'Get Form Schema',
      description: 'Download xf:* JSON',
      color: 'text-green-600'
    }
  ]

  return (
    <div className="min-h-[calc(100vh-200px)] flex flex-col justify-center">
      <div className="text-center">
        {/* Hero Section */}
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          SwiftForm AI
        </h1>

        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Transform documents into forms using AI
        </p>

        {/* CTA Button */}
        <button
          onClick={() => navigate('/upload')}
          className="inline-flex items-center px-6 py-3 text-lg font-medium rounded-lg
            text-white bg-primary-600 hover:bg-primary-700
            transform transition-all duration-200 hover:scale-105
            shadow-lg hover:shadow-xl"
        >
          <CloudUpload className="mr-2 h-6 w-6" />
          Get Started
        </button>

        {/* Features Grid */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg
                  transition-shadow duration-200 border border-gray-200"
              >
                <div className={`inline-flex p-3 rounded-full bg-gray-50 mb-4 ${feature.color}`}>
                  <Icon className="h-8 w-8" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>

        {/* Additional Info */}
        <div className="mt-16 bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-8 max-w-4xl mx-auto">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Powered by Advanced AI
          </h2>
          <p className="text-gray-700 max-w-2xl mx-auto">
            Our platform uses OpenAI GPT models to accurately extract form structures
            from your documents. Train custom models on your specific form types for
            even better accuracy.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white text-gray-700">
              ✓ PDF Support
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white text-gray-700">
              ✓ Custom Training
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white text-gray-700">
              ✓ JSON Export
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-white text-gray-700">
              ✓ Real-time Processing
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage