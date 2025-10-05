import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

def analyze_surgery_data(file_path):

    # Read data
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    
    # Get unique surgery types
    surgery_types = df['Surgery Type'].unique()
    
    # Create a figure for all analyses
    fig = plt.figure(figsize=(20, 12))
    
    results = {}
    
    for idx, surgery_type in enumerate(surgery_types, 1):
        # Filter data for this surgery type
        data = df[df['Surgery Type'] == surgery_type]['Value (min)'].values
        
        # Sort data
        sorted_data = np.sort(data)
        n = len(data)
        
        # Calculate statistics
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        minimum = np.min(data)
        maximum = np.max(data)
        
        # Calculate normal distribution parameters
        # f(j-0.5)/n for normal probability
        j = np.arange(1, n + 1)
        cumulative_prob = (j - 0.5) / n
        
        # Calculate z-scores (inverse normal)
        norm_scores = stats.norm.ppf(cumulative_prob)
        
        # Create bins for histogram
        num_bins = int(np.sqrt(n)) + 1
        hist, bin_edges = np.histogram(data, bins=num_bins)
        bin_width = bin_edges[1] - bin_edges[0]
        
        # Calculate Oi (observed frequency), Ei (expected frequency)
        intervals = []
        for i in range(len(bin_edges) - 1):
            lower = bin_edges[i]
            upper = bin_edges[i + 1]
            
            # Observed frequency
            oi = hist[i]
            
            # Expected frequency (using normal distribution)
            prob_lower = stats.norm.cdf(lower, mean, std)
            prob_upper = stats.norm.cdf(upper, mean, std)
            ei = n * (prob_upper - prob_lower)
            
            intervals.append({
                'bin_lower': lower,
                'bin_upper': upper,
                'bin_width': bin_width,
                'Oi': oi,
                'Ei': ei,
                'Oi_Ei_sq': (oi - ei) ** 2,
                'chi_sq_component': (oi - ei) ** 2 / ei if ei > 0 else 0
            })
        
        # Calculate chi-square statistic
        chi_square = sum([item['chi_sq_component'] for item in intervals if item['Ei'] > 0])
        
        # Degrees of freedom (k - 1 - number of parameters estimated)
        # We estimated 2 parameters (mean and std), so df = k - 3
        df_chi = len([item for item in intervals if item['Ei'] > 0]) - 3
        
        # Store results
        results[surgery_type] = {
            'data': data,
            'sorted_data': sorted_data,
            'mean': mean,
            'std': std,
            'min': minimum,
            'max': maximum,
            'n': n,
            'cumulative_prob': cumulative_prob,
            'norm_scores': norm_scores,
            'intervals': intervals,
            'chi_square': chi_square,
            'df': df_chi,
            'bin_edges': bin_edges,
            'hist': hist
        }
        
        # Create subplots for each surgery type
        # Histogram
        ax1 = plt.subplot(len(surgery_types), 3, (idx-1)*3 + 1)
        ax1.bar(bin_edges[:-1], hist, width=bin_width, alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Value (min)')
        ax1.set_ylabel('Frequency')
        ax1.set_title(f'{surgery_type} - Histogram')
        ax1.grid(True, alpha=0.3)
        
        # Add normal curve overlay
        x_range = np.linspace(minimum, maximum, 100)
        normal_curve = n * bin_width * stats.norm.pdf(x_range, mean, std)
        ax1.plot(x_range, normal_curve, 'r-', linewidth=2, label='Normal Distribution')
        ax1.legend()
        
        # Q-Q Plot
        ax2 = plt.subplot(len(surgery_types), 3, (idx-1)*3 + 2)
        ax2.scatter(sorted_data, norm_scores, alpha=0.6)
        
        # Add reference line
        z = np.polyfit(sorted_data, norm_scores, 1)
        p = np.poly1d(z)
        ax2.plot(sorted_data, p(sorted_data), "r--", linewidth=2)
        
        ax2.set_xlabel('Sample Values')
        ax2.set_ylabel('Theoretical Quantiles')
        ax2.set_title(f'{surgery_type} - Q-Q Plot')
        ax2.grid(True, alpha=0.3)
        
        # Statistics text
        ax3 = plt.subplot(len(surgery_types), 3, (idx-1)*3 + 3)
        ax3.axis('off')
        
        stats_text = f"""
{surgery_type} Statistics:

Mean: {mean:.2f}
Std Dev: {std:.2f}
Min: {minimum:.2f}
Max: {maximum:.2f}
N: {n}

Chi-Square: {chi_square:.2f}
Degrees of Freedom: {df_chi}
        """
        
        ax3.text(0.1, 0.5, stats_text, fontsize=10, family='monospace',
                verticalalignment='center')
    
    plt.tight_layout()
    plt.savefig('surgery_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return results


def create_detailed_tables(results):
    """Create detailed tables similar to Excel output"""
    
    for surgery_type, data in results.items():
        print(f"\n{'='*80}")
        print(f"DETAILED ANALYSIS: {surgery_type}")
        print(f"{'='*80}\n")
        
        # Basic statistics
        print(f"Mean: {data['mean']:.4f}")
        print(f"Standard Deviation: {data['std']:.4f}")
        print(f"Min: {data['min']:.4f}")
        print(f"Max: {data['max']:.4f}")
        print(f"Sample Size: {data['n']}")
        
        # Create DataFrame for sorted data with calculations
        df_sorted = pd.DataFrame({
            'Value (min)': data['sorted_data'],
            'sorted': data['sorted_data'],
            '(j-0.5)/n': data['cumulative_prob'],
            'Norm S': data['norm_scores']
        })
        
        print(f"\n--- Sorted Data with Normal Scores ---")
        print(df_sorted.head(10))
        
        # Chi-square table
        df_chi = pd.DataFrame(data['intervals'])
        print(f"\n--- Chi-Square Goodness of Fit ---")
        print(df_chi[['bin_lower', 'bin_upper', 'Oi', 'Ei', 'chi_sq_component']])
        
        print(f"\nChi-Square Statistic: {data['chi_square']:.4f}")
        print(f"Degrees of Freedom: {data['df']}")
        
        # Export to Excel
        with pd.ExcelWriter(f'{surgery_type.replace(" ", "_")}_analysis.xlsx') as writer:
            df_sorted.to_excel(writer, sheet_name='Sorted_Data', index=False)
            df_chi.to_excel(writer, sheet_name='Chi_Square', index=False)


if __name__ == "__main__":
    
    file_path = 'surgery_data.xlsx'
    
    # Run analysis
    results = analyze_surgery_data(file_path)
    
    # Create detailed tables
    create_detailed_tables(results)
    
    print("\nAnalysis complete! Check 'surgery_analysis.png' for plots.")