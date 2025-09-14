/**
 * Investment Opportunity Card Component
 * 
 * Displays a single investment opportunity with key metrics, scores, and analysis.
 */

import React from 'react';
import {
  InvestmentOpportunity,
  OPPORTUNITY_TYPE_LABELS,
  RISK_LEVEL_LABELS
} from '@/types/opportunity';
import {
  formatMarketCap,
  formatPercentage,
  getRiskLevelColorClass,
  getOpportunityTypeColorClass,
  getScoreColorClass
} from '@/services/opportunity';

interface OpportunityCardProps {
  opportunity: InvestmentOpportunity;
  onClick?: () => void;
  showDetails?: boolean;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onClick,
  showDetails = false
}) => {
  const {
    symbol,
    name,
    sector,
    currentPrice,
    marketCap,
    opportunityTypes,
    riskLevel,
    scores,
    keyMetrics,
    reasons,
    risks,
    priceTargetShort,
    priceTargetMedium,
    priceTargetLong
  } = opportunity;

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  };

  const calculateUpside = (targetPrice?: number) => {
    if (!targetPrice) return null;
    return ((targetPrice - currentPrice) / currentPrice) * 100;
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:shadow-md hover:border-blue-300' : ''
      }`}
      onClick={handleClick}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
          <p className="text-sm text-gray-600 truncate" title={name}>
            {name}
          </p>
          {sector && (
            <p className="text-xs text-gray-500 mt-1">{sector}</p>
          )}
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-gray-900">
            {formatPrice(currentPrice)}
          </div>
          {marketCap && (
            <div className="text-xs text-gray-500">
              {formatMarketCap(marketCap)}
            </div>
          )}
        </div>
      </div>

      {/* Score */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">Overall Score</span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColorClass(scores.overallScore)}`}>
            {scores.overallScore}/100
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              scores.overallScore >= 80 ? 'bg-green-500' :
              scores.overallScore >= 60 ? 'bg-yellow-500' :
              scores.overallScore >= 40 ? 'bg-orange-500' : 'bg-red-500'
            }`}
            style={{ width: `${scores.overallScore}%` }}
          />
        </div>
      </div>

      {/* Opportunity Types */}
      <div className="mb-3">
        <div className="flex flex-wrap gap-1">
          {opportunityTypes.slice(0, 3).map((type) => (
            <span
              key={type}
              className={`px-2 py-1 rounded-full text-xs font-medium ${getOpportunityTypeColorClass(type)}`}
            >
              {OPPORTUNITY_TYPE_LABELS[type]}
            </span>
          ))}
          {opportunityTypes.length > 3 && (
            <span className="px-2 py-1 rounded-full text-xs font-medium text-gray-600 bg-gray-100">
              +{opportunityTypes.length - 3} more
            </span>
          )}
        </div>
      </div>

      {/* Risk Level */}
      <div className="mb-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Risk Level</span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColorClass(riskLevel)}`}>
            {RISK_LEVEL_LABELS[riskLevel]}
          </span>
        </div>
      </div>

      {/* Key Metrics */}
      {Object.keys(keyMetrics).length > 0 && (
        <div className="mb-3">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Key Metrics</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(keyMetrics).slice(0, 4).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-600 capitalize">
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:
                </span>
                <span className="font-medium text-gray-900">
                  {typeof value === 'number' && key.includes('ratio') ? value.toFixed(2) :
                   typeof value === 'number' && (key.includes('growth') || key.includes('margin') || key.includes('roe')) ? 
                   formatPercentage(value) : value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Price Targets */}
      {(priceTargetShort || priceTargetMedium || priceTargetLong) && (
        <div className="mb-3">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Price Targets</h4>
          <div className="space-y-1 text-xs">
            {priceTargetShort && (
              <div className="flex justify-between">
                <span className="text-gray-600">3M Target:</span>
                <span className="font-medium text-gray-900">
                  {formatPrice(priceTargetShort)}
                  <span className="text-green-600 ml-1">
                    (+{calculateUpside(priceTargetShort)?.toFixed(1)}%)
                  </span>
                </span>
              </div>
            )}
            {priceTargetMedium && (
              <div className="flex justify-between">
                <span className="text-gray-600">6M Target:</span>
                <span className="font-medium text-gray-900">
                  {formatPrice(priceTargetMedium)}
                  <span className="text-green-600 ml-1">
                    (+{calculateUpside(priceTargetMedium)?.toFixed(1)}%)
                  </span>
                </span>
              </div>
            )}
            {priceTargetLong && (
              <div className="flex justify-between">
                <span className="text-gray-600">12M Target:</span>
                <span className="font-medium text-gray-900">
                  {formatPrice(priceTargetLong)}
                  <span className="text-green-600 ml-1">
                    (+{calculateUpside(priceTargetLong)?.toFixed(1)}%)
                  </span>
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Detailed Analysis (if showDetails is true) */}
      {showDetails && (
        <>
          {/* Detailed Scores */}
          {(scores.fundamentalScore || scores.technicalScore || scores.valueScore || scores.qualityScore) && (
            <div className="mb-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Detailed Scores</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {scores.fundamentalScore && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Fundamental:</span>
                    <span className="font-medium text-gray-900">{scores.fundamentalScore}/100</span>
                  </div>
                )}
                {scores.technicalScore && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Technical:</span>
                    <span className="font-medium text-gray-900">{scores.technicalScore}/100</span>
                  </div>
                )}
                {scores.valueScore && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Value:</span>
                    <span className="font-medium text-gray-900">{scores.valueScore}/100</span>
                  </div>
                )}
                {scores.qualityScore && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Quality:</span>
                    <span className="font-medium text-gray-900">{scores.qualityScore}/100</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Reasons */}
          {reasons.length > 0 && (
            <div className="mb-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Why It's an Opportunity</h4>
              <ul className="text-xs text-gray-600 space-y-1">
                {reasons.slice(0, 3).map((reason, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-green-500 mr-1">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
                {reasons.length > 3 && (
                  <li className="text-gray-500 italic">
                    +{reasons.length - 3} more reasons...
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Risks */}
          {risks.length > 0 && (
            <div className="mb-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Key Risks</h4>
              <ul className="text-xs text-gray-600 space-y-1">
                {risks.slice(0, 2).map((risk, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-red-500 mr-1">•</span>
                    <span>{risk}</span>
                  </li>
                ))}
                {risks.length > 2 && (
                  <li className="text-gray-500 italic">
                    +{risks.length - 2} more risks...
                  </li>
                )}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="pt-3 border-t border-gray-100">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>
            Updated: {new Date(opportunity.lastUpdated).toLocaleDateString()}
          </span>
          {onClick && (
            <span className="text-blue-600 hover:text-blue-700">
              View Details →
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default OpportunityCard;