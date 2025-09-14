/**
 * Disclaimer Service
 * 
 * Centralized service for managing disclaimers, risk warnings, and legal text
 * throughout the application.
 */

export interface DisclaimerConfig {
  id: string;
  title: string;
  content: string;
  severity: 'info' | 'warning' | 'error';
  required: boolean;
  contexts: DisclaimerContext[];
}

export type DisclaimerContext = 
  | 'chat_response'
  | 'analysis_result'
  | 'recommendation'
  | 'backtest'
  | 'export'
  | 'shared_analysis'
  | 'watchlist'
  | 'alert'
  | 'app_startup'
  | 'terms_of_use'
  | 'privacy_policy';

export interface UserAcknowledgment {
  userId: string;
  disclaimerId: string;
  acknowledgedAt: Date;
  version: string;
}

class DisclaimerService {
  private disclaimers: DisclaimerConfig[] = [
    {
      id: 'investment_advice',
      title: 'Investment Disclaimer',
      content: `This application provides information and analysis for educational purposes only and does not constitute investment advice, financial advice, trading advice, or any other sort of advice. The information provided should not be relied upon as a substitute for extensive independent market research before making your investment decisions. All investments carry risk of loss, and you may lose some or all of your investment. Past performance does not guarantee future results.`,
      severity: 'warning',
      required: true,
      contexts: ['chat_response', 'analysis_result', 'recommendation', 'export', 'shared_analysis']
    },
    {
      id: 'data_accuracy',
      title: 'Data Accuracy Disclaimer',
      content: `The data and information provided in this application is obtained from sources believed to be reliable, but we cannot guarantee its accuracy, completeness, or timeliness. Market data may be delayed, and real-time quotes may not be available. Users should verify all information independently before making investment decisions.`,
      severity: 'info',
      required: false,
      contexts: ['analysis_result', 'export', 'shared_analysis', 'chat_response']
    },
    {
      id: 'risk_warning',
      title: 'Risk Warning',
      content: `Trading and investing in stocks, securities, and financial instruments involves substantial risk of loss and is not suitable for all investors. Stock prices can be extremely volatile and unpredictable. You should carefully consider your investment objectives, level of experience, and risk appetite before making any investment decisions. Never invest money you cannot afford to lose.`,
      severity: 'error',
      required: true,
      contexts: ['recommendation', 'analysis_result', 'backtest', 'app_startup']
    },
    {
      id: 'ai_limitations',
      title: 'AI Analysis Limitations',
      content: `This application uses artificial intelligence and automated analysis tools. AI-generated content may contain errors, biases, or inaccuracies. The analysis is based on historical data and patterns, which may not predict future market behavior. Always conduct your own research and consult with qualified financial professionals before making investment decisions.`,
      severity: 'warning',
      required: true,
      contexts: ['chat_response', 'analysis_result', 'recommendation']
    },
    {
      id: 'backtesting_limitations',
      title: 'Backtesting Disclaimer',
      content: `Backtesting results are hypothetical and do not represent actual trading. Past performance shown in backtests does not guarantee future results. Backtesting may not account for market impact, liquidity constraints, transaction costs, slippage, or other real-world trading conditions. Actual trading results may differ significantly from backtested results.`,
      severity: 'warning',
      required: true,
      contexts: ['backtest']
    },
    {
      id: 'no_fiduciary_duty',
      title: 'No Fiduciary Relationship',
      content: `The use of this application does not create a fiduciary relationship between you and the application providers. We are not acting as your financial advisor, investment advisor, or in any fiduciary capacity. You are solely responsible for your investment decisions.`,
      severity: 'info',
      required: false,
      contexts: ['app_startup', 'terms_of_use']
    },
    {
      id: 'regulatory_compliance',
      title: 'Regulatory Notice',
      content: `This application is not registered as an investment advisor or broker-dealer. The information provided is not personalized investment advice. Users are responsible for complying with all applicable laws and regulations in their jurisdiction regarding investment activities.`,
      severity: 'warning',
      required: true,
      contexts: ['app_startup', 'terms_of_use']
    },
    {
      id: 'market_volatility',
      title: 'Market Volatility Warning',
      content: `Financial markets are subject to extreme volatility and unpredictable events. Market conditions can change rapidly, and investments can lose value quickly. Economic events, geopolitical situations, and market sentiment can significantly impact investment performance in ways that cannot be predicted or modeled.`,
      severity: 'error',
      required: true,
      contexts: ['recommendation', 'analysis_result', 'high_risk_stocks']
    }
  ];

  private userAcknowledgments: Map<string, UserAcknowledgment[]> = new Map();

  /**
   * Get disclaimers for a specific context
   */
  getDisclaimersForContext(context: DisclaimerContext): DisclaimerConfig[] {
    return this.disclaimers.filter(disclaimer => 
      disclaimer.contexts.includes(context)
    );
  }

  /**
   * Get required disclaimers for a context
   */
  getRequiredDisclaimersForContext(context: DisclaimerContext): DisclaimerConfig[] {
    return this.getDisclaimersForContext(context).filter(disclaimer => disclaimer.required);
  }

  /**
   * Check if user has acknowledged required disclaimers for a context
   */
  hasUserAcknowledgedContext(userId: string, context: DisclaimerContext): boolean {
    const requiredDisclaimers = this.getRequiredDisclaimersForContext(context);
    const userAcks = this.userAcknowledgments.get(userId) || [];
    
    return requiredDisclaimers.every(disclaimer => 
      userAcks.some(ack => 
        ack.disclaimerId === disclaimer.id && 
        this.isAcknowledgmentValid(ack)
      )
    );
  }

  /**
   * Record user acknowledgment of a disclaimer
   */
  acknowledgeDisclaimer(userId: string, disclaimerId: string): void {
    const userAcks = this.userAcknowledgments.get(userId) || [];
    
    // Remove any existing acknowledgment for this disclaimer
    const filteredAcks = userAcks.filter(ack => ack.disclaimerId !== disclaimerId);
    
    // Add new acknowledgment
    filteredAcks.push({
      userId,
      disclaimerId,
      acknowledgedAt: new Date(),
      version: '1.0' // Version for tracking disclaimer changes
    });
    
    this.userAcknowledgments.set(userId, filteredAcks);
    
    // Persist to localStorage
    this.persistAcknowledgments(userId);
  }

  /**
   * Load user acknowledgments from localStorage
   */
  loadUserAcknowledgments(userId: string): void {
    try {
      const stored = localStorage.getItem(`disclaimers_${userId}`);
      if (stored) {
        const acknowledgments = JSON.parse(stored).map((ack: any) => ({
          ...ack,
          acknowledgedAt: new Date(ack.acknowledgedAt)
        }));
        this.userAcknowledgments.set(userId, acknowledgments);
      }
    } catch (error) {
      console.error('Failed to load user acknowledgments:', error);
    }
  }

  /**
   * Persist user acknowledgments to localStorage
   */
  private persistAcknowledgments(userId: string): void {
    try {
      const acknowledgments = this.userAcknowledgments.get(userId) || [];
      localStorage.setItem(`disclaimers_${userId}`, JSON.stringify(acknowledgments));
    } catch (error) {
      console.error('Failed to persist user acknowledgments:', error);
    }
  }

  /**
   * Check if an acknowledgment is still valid (not expired)
   */
  private isAcknowledgmentValid(acknowledgment: UserAcknowledgment): boolean {
    const maxAge = 365 * 24 * 60 * 60 * 1000; // 1 year in milliseconds
    const age = Date.now() - acknowledgment.acknowledgedAt.getTime();
    return age < maxAge;
  }

  /**
   * Get disclaimer by ID
   */
  getDisclaimer(id: string): DisclaimerConfig | undefined {
    return this.disclaimers.find(disclaimer => disclaimer.id === id);
  }

  /**
   * Get all disclaimers
   */
  getAllDisclaimers(): DisclaimerConfig[] {
    return [...this.disclaimers];
  }

  /**
   * Generate disclaimer text for embedding in responses
   */
  generateDisclaimerText(context: DisclaimerContext, compact: boolean = false): string {
    const disclaimers = this.getRequiredDisclaimersForContext(context);
    
    if (disclaimers.length === 0) {
      return '';
    }

    if (compact) {
      return `⚠️ Important: This is for informational purposes only and not investment advice. All investments carry risk of loss.`;
    }

    const disclaimerTexts = disclaimers.map(disclaimer => 
      `**${disclaimer.title}:** ${disclaimer.content}`
    );

    return `\n\n---\n**IMPORTANT DISCLAIMERS:**\n\n${disclaimerTexts.join('\n\n')}`;
  }

  /**
   * Check if high-risk disclaimer should be shown
   */
  shouldShowHighRiskDisclaimer(riskLevel?: string, volatility?: number): boolean {
    if (riskLevel === 'HIGH' || riskLevel === 'VERY_HIGH') {
      return true;
    }
    
    if (volatility && volatility > 0.3) { // 30% volatility threshold
      return true;
    }
    
    return false;
  }

  /**
   * Get terms of use text
   */
  getTermsOfUse(): string {
    return `
# Terms of Use

## Acceptance of Terms
By using Settlers of Stock, you agree to be bound by these Terms of Use and all applicable laws and regulations.

## Service Description
Settlers of Stock is a stock research and analysis application that provides educational information about financial markets and securities. The service is provided "as is" without warranties of any kind.

## Investment Disclaimer
${this.getDisclaimer('investment_advice')?.content}

## Data and Information
${this.getDisclaimer('data_accuracy')?.content}

## Risk Acknowledgment
${this.getDisclaimer('risk_warning')?.content}

## AI and Automated Analysis
${this.getDisclaimer('ai_limitations')?.content}

## No Fiduciary Relationship
${this.getDisclaimer('no_fiduciary_duty')?.content}

## Regulatory Compliance
${this.getDisclaimer('regulatory_compliance')?.content}

## Limitation of Liability
In no event shall Settlers of Stock or its providers be liable for any direct, indirect, incidental, special, or consequential damages arising from the use of this service.

## User Responsibilities
- You are solely responsible for your investment decisions
- You must comply with all applicable laws and regulations
- You must not rely solely on this application for investment decisions
- You should consult with qualified financial professionals

## Modifications
These terms may be updated from time to time. Continued use of the service constitutes acceptance of any modifications.

Last Updated: ${new Date().toLocaleDateString()}
    `.trim();
  }

  /**
   * Get privacy policy text
   */
  getPrivacyPolicy(): string {
    return `
# Privacy Policy

## Information We Collect
- Account information (email, preferences)
- Usage data (queries, analysis requests)
- Technical data (IP address, browser information)
- Chat history and watchlists

## How We Use Information
- To provide stock analysis and research services
- To improve our algorithms and user experience
- To send notifications and alerts (with your consent)
- To comply with legal obligations

## Data Storage and Security
- Data is stored securely using industry-standard encryption
- We use Google Cloud Platform for data storage and processing
- Chat history is stored for service improvement and context
- Financial data is sourced from third-party providers

## Data Sharing
We do not sell or share your personal information with third parties except:
- As required by law or legal process
- To protect our rights or the safety of users
- With service providers who assist in operating our platform

## Your Rights
- Access your personal data
- Correct inaccurate information
- Delete your account and associated data
- Export your data in a portable format

## Cookies and Tracking
We use cookies and similar technologies to:
- Maintain your session and preferences
- Analyze usage patterns
- Provide personalized experiences

## Data Retention
- Account data: Retained while your account is active
- Chat history: Retained for 2 years for service improvement
- Usage analytics: Retained for 1 year in aggregated form

## Contact Information
For privacy-related questions or requests, contact us at privacy@settlersofstock.com

## Changes to Privacy Policy
We may update this policy from time to time. We will notify users of significant changes.

Last Updated: ${new Date().toLocaleDateString()}
    `.trim();
  }
}

export const disclaimerService = new DisclaimerService();