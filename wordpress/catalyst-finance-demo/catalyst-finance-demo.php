<?php
/**
 * Plugin Name: Catalyst Finance Demo
 * Description: Persistent finance workspace with modeling, evidence, review, governance, redaction, and publication workflows for Sustainable Catalyst.
 * Version: 2.0.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

define('CATALYST_FINANCE_DEMO_VERSION', '2.0.0');

function catalyst_finance_demo_assets() {
    $base = plugin_dir_url(__FILE__);
    wp_enqueue_style(
        'catalyst-finance-demo',
        $base . 'assets/catalyst-finance-demo.css',
        array(),
        CATALYST_FINANCE_DEMO_VERSION
    );
    wp_enqueue_script(
        'catalyst-finance-engine',
        $base . 'assets/catalyst-finance-engine.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-cashflow-engine',
        $base . 'assets/catalyst-finance-cashflow-engine.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-comparison-engine',
        $base . 'assets/catalyst-finance-comparison-engine.js',
        array('catalyst-finance-cashflow-engine'),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-uncertainty-engine',
        $base . 'assets/catalyst-finance-uncertainty-engine.js',
        array('catalyst-finance-cashflow-engine', 'catalyst-finance-comparison-engine'),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-pricing-engine',
        $base . 'assets/catalyst-finance-pricing-engine.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-operating-engine',
        $base . 'assets/catalyst-finance-operating-engine.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-sustainable-engine',
        $base . 'assets/catalyst-finance-sustainable-engine.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-platform-engine',
        $base . 'assets/catalyst-finance-platform-engine.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-governance-engine',
        $base . 'assets/catalyst-finance-governance-engine.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
    wp_enqueue_script(
        'catalyst-finance-demo',
        $base . 'assets/catalyst-finance-demo.js',
        array('catalyst-finance-engine', 'catalyst-finance-cashflow-engine', 'catalyst-finance-comparison-engine', 'catalyst-finance-uncertainty-engine', 'catalyst-finance-pricing-engine', 'catalyst-finance-operating-engine', 'catalyst-finance-sustainable-engine', 'catalyst-finance-governance-engine', 'catalyst-finance-platform-engine'),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
}

function catalyst_finance_demo_shortcode($atts = array()) {
    $atts = shortcode_atts(
        array('mode' => 'workspace'),
        $atts,
        'catalyst_finance_demo'
    );
    $mode = $atts['mode'] === 'public' ? 'public' : 'workspace';
    catalyst_finance_demo_assets();
    ob_start();
    ?>
    <section class="scfin-demo" data-scfin-demo data-scfin-mode="<?php echo esc_attr($mode); ?>">
      <div class="scfin-demo__header">
        <p class="scfin-demo__eyebrow">Catalyst Finance v2.0.0</p>
        <h3><?php echo $mode === 'public' ? 'Explore a finance scenario' : 'Persistent finance scenario workspace'; ?></h3>
        <p><?php echo $mode === 'public'
            ? 'Review a read-only example using the canonical finance screening model.'
            : 'Create alternatives, preserve revision history, recover interrupted work, and export or import the complete workspace.'; ?></p>
      </div>

      <?php if ($mode === 'workspace') : ?>
      <div class="scfin-demo__workspace" data-scfin-workspace-controls>
        <label class="scfin-demo__workspace-name">
          <span>Workspace</span>
          <input type="text" value="My finance workspace" data-scfin-workspace-name>
        </label>
        <label>
          <span>Scenario</span>
          <select data-scfin-scenario-select aria-label="Select scenario"></select>
        </label>
        <label>
          <span>Template</span>
          <select data-scfin-template-select>
            <option value="capital-project">Capital project</option>
            <option value="operating-change">Operating change</option>
            <option value="pricing-decision">Pricing decision</option>
            <option value="sustainability-investment">Sustainability investment</option>
            <option value="public-value-initiative">Public-value initiative</option>
          </select>
        </label>
        <div class="scfin-demo__workspace-actions">
          <button type="button" data-scfin-new>New</button>
          <button type="button" data-scfin-duplicate>Duplicate</button>
          <button type="button" data-scfin-rename>Rename</button>
          <button type="button" data-scfin-save>Save revision</button>
          <button type="button" data-scfin-archive>Archive</button>
          <button type="button" data-scfin-restore>Restore</button>
          <button type="button" data-scfin-delete>Delete</button>
        </div>
        <div class="scfin-demo__workspace-files">
          <button type="button" data-scfin-export-workspace>Export workspace</button>
          <label class="scfin-demo__file-label">
            <span>Import workspace</span>
            <input type="file" accept="application/json,.json" data-scfin-import-workspace>
          </label>
        </div>
        <p class="scfin-demo__save-status" data-scfin-save-status role="status">Saved locally</p>
      </div>
      <?php endif; ?>

      <div class="scfin-demo__grid">
        <form class="scfin-demo__form" data-scfin-form>
          <label>
            <span>Initiative</span>
            <input name="projectName" type="text" value="Building efficiency retrofit">
          </label>

          <div class="scfin-demo__two">
            <label>
              <span>Category</span>
              <input name="category" type="text" value="Energy efficiency">
            </label>
            <label>
              <span>Alternative</span>
              <input name="alternativeLabel" type="text" value="Base">
            </label>
          </div>

          <div class="scfin-demo__two">
            <label>
              <span>Capital cost ($)</span>
              <input name="capitalCost" type="number" min="0" step="1000" value="250000">
            </label>
            <label>
              <span>Grant / funding ($)</span>
              <input name="externalFunding" type="number" min="0" step="1000" value="40000">
            </label>
          </div>

          <div class="scfin-demo__two">
            <label>
              <span>Annual savings ($)</span>
              <input name="annualSavings" type="number" min="0" step="1000" value="52000">
            </label>
            <label>
              <span>Annual operating cost ($)</span>
              <input name="annualOperatingCost" type="number" min="0" step="500" value="7000">
            </label>
          </div>

          <div class="scfin-demo__two">
            <label>
              <span>Time horizon (years)</span>
              <input name="timeHorizon" type="number" min="0.1" max="100" step="0.1" value="10">
            </label>
            <label>
              <span>Discount rate (%)</span>
              <input name="discountRate" type="number" min="-99.9" max="100" step="0.1" value="6">
            </label>
          </div>

          <div class="scfin-demo__two">
            <label>
              <span>Annual emissions reduced (tons)</span>
              <input name="annualEmissions" type="number" min="0" step="1" value="180">
            </label>
            <label>
              <span>Carbon value ($/ton)</span>
              <input name="carbonPrice" type="number" min="0" step="1" value="35">
            </label>
          </div>

          <label>
            <span>Evidence confidence: <strong data-scfin-confidence-label>72</strong>%</span>
            <input name="confidence" type="range" min="0" max="100" value="72">
          </label>

          <label>
            <span>Implementation risk: <strong data-scfin-risk-label>34</strong>%</span>
            <input name="implementationRisk" type="range" min="0" max="100" value="34">
          </label>

          <div class="scfin-demo__two">
            <label>
              <span>Tags</span>
              <input name="tags" type="text" value="retrofit, energy">
            </label>
            <label>
              <span>Notes</span>
              <textarea name="notes" rows="3">Initial screening case.</textarea>
            </label>
          </div>

          <div class="scfin-demo__actions">
            <button type="button" data-scfin-copy>Copy JSON</button>
            <button type="button" data-scfin-download>Download scenario</button>
            <button type="button" data-scfin-print>Print / PDF</button>
          </div>
        </form>

        <div class="scfin-demo__output" aria-live="polite">
          <div class="scfin-demo__metrics">
            <div><span>NPV</span><strong data-scfin-npv>$0</strong></div>
            <div><span>Payback</span><strong data-scfin-payback>—</strong></div>
            <div><span>ROI estimate</span><strong data-scfin-roi>0%</strong></div>
            <div><span>Risk score</span><strong data-scfin-score>0/100</strong></div>
          </div>

          <canvas class="scfin-demo__chart" width="760" height="260" data-scfin-chart aria-label="Cumulative cash flow chart"></canvas>

          <div class="scfin-demo__brief">
            <h4 data-scfin-level>Review level</h4>
            <p data-scfin-note></p>
            <ul data-scfin-flags></ul>
          </div>

          <details class="scfin-demo__details">
            <summary>Score methodology</summary>
            <ul data-scfin-score-trace></ul>
          </details>

          <details class="scfin-demo__details">
            <summary>Contract-valid JSON export</summary>
            <pre data-scfin-json></pre>
          </details>
        </div>
      </div>

      <section class="scfin-capital" data-scfin-capital-budgeting>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Period cash-flow model</p>
          <h3>Capital budgeting studio</h3>
          <p>Build a period-level case with phased capital, recurring benefits and costs, working capital, terminal value, and explicit nominal or real assumptions.</p>
        </div>
        <div class="scfin-capital__layout">
          <form class="scfin-capital__form" data-scfin-cf-form>
            <div class="scfin-demo__two">
              <label><span>Frequency</span><select name="frequency"><option value="annual">Annual</option><option value="quarterly">Quarterly</option><option value="monthly">Monthly</option></select></label>
              <label><span>Horizon (periods)</span><input name="horizon" type="number" min="1" max="1200" value="10"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Price basis</span><select name="basis"><option value="nominal">Nominal</option><option value="real">Real</option></select></label>
              <label><span>Annual discount rate (%)</span><input name="discountRate" type="number" min="-99" max="1000" step="0.1" value="6"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Initial capital cost</span><input name="capitalCost" type="number" min="0" step="1000" value="250000"></label>
              <label><span>Grant / rebate</span><input name="grant" type="number" min="0" step="1000" value="40000"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Recurring benefit per period</span><input name="benefit" type="number" min="0" step="1000" value="60000"></label>
              <label><span>Recurring operating cost</span><input name="operatingCost" type="number" min="0" step="500" value="10000"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Annual escalation (%)</span><input name="escalation" type="number" min="-99" max="1000" step="0.1" value="2"></label>
              <label><span>Phased capital in period 2</span><input name="phasedCapital" type="number" min="0" step="1000" value="0"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Working capital at period 0</span><input name="workingCapital" type="number" min="0" step="1000" value="15000"></label>
              <label><span>Working-capital recovery</span><input name="workingCapitalRecovery" type="number" min="0" step="1000" value="15000"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Residual value</span><input name="residualValue" type="number" min="0" step="1000" value="20000"></label>
              <label><span>Decommissioning cost</span><input name="decommissioningCost" type="number" min="0" step="1000" value="5000"></label>
            </div>
            <div class="scfin-demo__actions">
              <button type="button" data-scfin-cf-download>Download analysis</button>
              <button type="button" data-scfin-cf-copy>Copy JSON</button>
            </div>
          </form>
          <div class="scfin-capital__output" aria-live="polite">
            <div class="scfin-demo__metrics scfin-capital__metrics">
              <div><span>NPV</span><strong data-scfin-cf-npv>—</strong></div>
              <div><span>Payback</span><strong data-scfin-cf-payback>—</strong></div>
              <div><span>IRR / MIRR</span><strong data-scfin-cf-irr>—</strong></div>
              <div><span>BCR / EAV</span><strong data-scfin-cf-bcr>—</strong></div>
            </div>
            <div class="scfin-capital__charts">
              <figure><figcaption>Cumulative cash flow</figcaption><canvas width="760" height="250" data-scfin-cf-curve></canvas></figure>
              <figure><figcaption>Period waterfall</figcaption><canvas width="760" height="250" data-scfin-cf-waterfall></canvas></figure>
            </div>
            <div class="scfin-capital__table-wrap">
              <table class="scfin-capital__table">
                <thead><tr><th>Period</th><th>Inflows</th><th>Outflows</th><th>Net</th><th>Discounted</th><th>Cumulative</th></tr></thead>
                <tbody data-scfin-cf-table></tbody>
              </table>
            </div>
            <details class="scfin-demo__details" open><summary>Metric explanations and review flags</summary><ul data-scfin-cf-trace></ul></details>
            <details class="scfin-demo__details"><summary>Contract-valid capital-budgeting JSON</summary><pre data-scfin-cf-json></pre></details>
          </div>
        </div>
      </section>


      <section class="scfin-comparison" data-scfin-comparison-studio>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Alternative analysis</p>
          <h3>Scenario comparison and sensitivity studio</h3>
          <p>Compare downside, base, and upside revisions using aligned metrics, weighted rankings, financial dominance, sensitivity ranges, and reproducible break-even thresholds.</p>
        </div>
        <div class="scfin-comparison__actions">
          <button type="button" data-scfin-comparison-refresh>Refresh comparison</button>
          <button type="button" data-scfin-comparison-download>Download comparison bundle</button>
        </div>
        <div class="scfin-comparison__grid">
          <div class="scfin-comparison__panel">
            <h4>Ranked alternatives</h4>
            <div class="scfin-capital__table-wrap">
              <table class="scfin-capital__table scfin-comparison__table">
                <thead><tr><th>Rank</th><th>Alternative</th><th>Score</th><th>NPV</th><th>Discounted payback</th><th>Dominance</th></tr></thead>
                <tbody data-scfin-comparison-ranking></tbody>
              </table>
            </div>
          </div>
          <div class="scfin-comparison__panel">
            <h4>Aligned metric deltas</h4>
            <div class="scfin-capital__table-wrap">
              <table class="scfin-capital__table scfin-comparison__table">
                <thead><tr><th>Metric</th><th>Downside</th><th>Base</th><th>Upside</th></tr></thead>
                <tbody data-scfin-comparison-metrics></tbody>
              </table>
            </div>
          </div>
          <div class="scfin-comparison__panel">
            <h4>Tornado sensitivity</h4>
            <canvas width="760" height="300" data-scfin-comparison-tornado aria-label="Sensitivity tornado chart"></canvas>
            <ul data-scfin-comparison-tornado-list></ul>
          </div>
          <div class="scfin-comparison__panel">
            <h4>Break-even thresholds</h4>
            <ul data-scfin-comparison-thresholds></ul>
            <h4>Non-financial caveats</h4>
            <ul data-scfin-comparison-caveats></ul>
          </div>
        </div>
        <details class="scfin-demo__details"><summary>Versioned comparison artifact</summary><pre data-scfin-comparison-json></pre></details>
      </section>

      <section class="scfin-uncertainty" data-scfin-uncertainty-studio>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Probability and adverse cases</p>
          <h3>Uncertainty, Monte Carlo, and stress-testing studio</h3>
          <p>Run a seeded simulation around the live capital-budgeting case, inspect downside probabilities and variable influence, and compare named multi-factor stress cases.</p>
        </div>
        <div class="scfin-uncertainty__controls">
          <label><span>Iterations</span><input type="number" min="100" max="5000" step="100" value="500" data-scfin-uncertainty-iterations></label>
          <label><span>Seed</span><input type="number" min="0" max="4294967295" step="1" value="20260717" data-scfin-uncertainty-seed></label>
          <label><span>Capital range (%)</span><input type="number" min="1" max="100" step="1" value="20" data-scfin-uncertainty-capital></label>
          <label><span>Benefit standard deviation (%)</span><input type="number" min="1" max="100" step="1" value="15" data-scfin-uncertainty-benefit></label>
          <button type="button" data-scfin-uncertainty-run>Run seeded simulation</button>
          <button type="button" data-scfin-uncertainty-download>Download uncertainty bundle</button>
        </div>
        <div class="scfin-uncertainty__metrics">
          <div><span>Mean NPV</span><strong data-scfin-uncertainty-mean>—</strong></div>
          <div><span>NPV P5</span><strong data-scfin-uncertainty-p5>—</strong></div>
          <div><span>Probability NPV &gt; 0</span><strong data-scfin-uncertainty-positive>—</strong></div>
          <div><span>Expected shortfall</span><strong data-scfin-uncertainty-shortfall>—</strong></div>
        </div>
        <div class="scfin-uncertainty__grid">
          <div class="scfin-comparison__panel">
            <h4>NPV distribution</h4>
            <canvas width="760" height="280" data-scfin-uncertainty-histogram aria-label="Monte Carlo NPV histogram"></canvas>
          </div>
          <div class="scfin-comparison__panel">
            <h4>Variable influence</h4>
            <ol data-scfin-uncertainty-influence></ol>
          </div>
          <div class="scfin-comparison__panel">
            <h4>Stress cases</h4>
            <ul data-scfin-uncertainty-stress></ul>
          </div>
          <div class="scfin-comparison__panel">
            <h4>Reproducibility</h4>
            <p data-scfin-uncertainty-meta>Run the simulation to record the seed and completed iterations.</p>
          </div>
        </div>
        <details class="scfin-demo__details"><summary>Versioned uncertainty publication</summary><pre data-scfin-uncertainty-json></pre></details>
      </section>

      <section class="scfin-pricing" data-scfin-pricing-studio>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Demand and revenue analysis</p>
          <h3>Pricing and elasticity studio</h3>
          <p>Model segmented demand, cost-to-serve, capacity, break-even volume, and revenue, contribution, or profit objectives across a transparent price grid.</p>
        </div>
        <div class="scfin-pricing__layout">
          <form class="scfin-pricing__form" data-scfin-pricing-form>
            <div class="scfin-demo__two">
              <label><span>Objective</span><select name="objective"><option value="profit">Profit</option><option value="contribution">Contribution</option><option value="revenue">Revenue</option></select></label>
              <label><span>Current price</span><input name="currentPrice" type="number" min="0.01" step="0.5" value="50"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Minimum price</span><input name="minimumPrice" type="number" min="0.01" step="0.5" value="30"></label>
              <label><span>Maximum price</span><input name="maximumPrice" type="number" min="0.01" step="0.5" value="80"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Commuter intercept</span><input name="intercept" type="number" min="1" step="100" value="18000"></label>
              <label><span>Commuter slope</span><input name="slope" type="number" min="0.01" step="1" value="180"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Hybrid demand at current price</span><input name="referenceQuantity" type="number" min="0" step="100" value="7000"></label>
              <label><span>Hybrid elasticity</span><input name="elasticity" type="number" max="-0.01" step="0.05" value="-1.35"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Unit variable cost</span><input name="unitCost" type="number" min="0" step="0.5" value="11.5"></label>
              <label><span>Fixed cost</span><input name="fixedCost" type="number" min="0" step="1000" value="350000"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Capacity units</span><input name="capacity" type="number" min="1" step="100" value="22000"></label>
              <label><span>Maximum price change (%)</span><input name="maxChange" type="number" min="0.1" step="0.5" value="20"></label>
            </div>
            <div class="scfin-demo__actions">
              <button type="button" data-scfin-pricing-run>Evaluate pricing</button>
              <button type="button" data-scfin-pricing-download>Download publication</button>
            </div>
          </form>
          <div class="scfin-pricing__output" aria-live="polite">
            <div class="scfin-demo__metrics">
              <div><span>Recommended price</span><strong data-scfin-pricing-price>—</strong></div>
              <div><span>Expected gain</span><strong data-scfin-pricing-gain>—</strong></div>
              <div><span>Recommended volume</span><strong data-scfin-pricing-volume>—</strong></div>
              <div><span>Average elasticity</span><strong data-scfin-pricing-elasticity>—</strong></div>
            </div>
            <p class="scfin-pricing__recommendation" data-scfin-pricing-note></p>
            <canvas width="760" height="280" data-scfin-pricing-chart aria-label="Pricing objective curve"></canvas>
            <div class="scfin-capital__table-wrap">
              <table class="scfin-capital__table"><thead><tr><th>Price</th><th>Quantity</th><th>Revenue</th><th>Contribution</th><th>Profit</th><th>Elasticity</th></tr></thead><tbody data-scfin-pricing-table></tbody></table>
            </div>
            <ul data-scfin-pricing-flags></ul>
            <details class="scfin-demo__details"><summary>Versioned pricing publication</summary><pre data-scfin-pricing-json></pre></details>
          </div>
        </div>
      </section>

      <section class="scfin-operating" data-scfin-operating-studio>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Budget and cost control</p>
          <h3>Operating economics studio</h3>
          <p>Reconcile a static budget, flexible budget, and actual result while reviewing contribution margin, break-even volume, margin of safety, operating leverage, and favorable or unfavorable variances.</p>
        </div>
        <div class="scfin-operating__layout">
          <form class="scfin-operating__form" data-scfin-operating-form>
            <div class="scfin-demo__two">
              <label><span>Budget units</span><input name="budgetUnits" type="number" min="0" step="1" value="120"></label>
              <label><span>Actual units</span><input name="actualUnits" type="number" min="0" step="1" value="130"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Budget price</span><input name="budgetPrice" type="number" min="0" step="1" value="600"></label>
              <label><span>Actual price</span><input name="actualPrice" type="number" min="0" step="1" value="620"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Budget variable cost / unit</span><input name="budgetVariable" type="number" min="0" step="1" value="280"></label>
              <label><span>Actual variable cost / unit</span><input name="actualVariable" type="number" min="0" step="1" value="290"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Budget fixed + overhead</span><input name="budgetFixed" type="number" min="0" step="100" value="25000"></label>
              <label><span>Actual fixed + overhead</span><input name="actualFixed" type="number" min="0" step="100" value="25700"></label>
            </div>
            <label><span>Target operating profit</span><input name="targetProfit" type="number" step="100" value="25000"></label>
            <div class="scfin-demo__actions">
              <button type="button" data-scfin-operating-run>Evaluate operations</button>
              <button type="button" data-scfin-operating-download>Download publication</button>
            </div>
          </form>
          <div class="scfin-operating__output" aria-live="polite">
            <div class="scfin-demo__metrics">
              <div><span>Actual operating profit</span><strong data-scfin-operating-profit>—</strong></div>
              <div><span>Profit variance</span><strong data-scfin-operating-variance>—</strong></div>
              <div><span>Break-even units</span><strong data-scfin-operating-breakeven>—</strong></div>
              <div><span>Margin of safety</span><strong data-scfin-operating-safety>—</strong></div>
            </div>
            <div class="scfin-capital__table-wrap">
              <table class="scfin-capital__table"><thead><tr><th>Variance</th><th>Amount</th><th>Status</th></tr></thead><tbody data-scfin-operating-table></tbody></table>
            </div>
            <ul data-scfin-operating-flags></ul>
            <details class="scfin-demo__details"><summary>Versioned operating publication</summary><pre data-scfin-operating-json></pre></details>
          </div>
        </div>
      </section>

      <section class="scfin-sustainable" data-scfin-sustainable-studio>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Carbon and natural capital</p>
          <h3>Sustainable finance studio</h3>
          <p>Reconcile avoided emissions, one selected carbon-value basis, natural-capital value, transition effects, and green-financing savings without double counting.</p>
        </div>
        <div class="scfin-sustainable__layout">
          <form class="scfin-sustainable__form" data-scfin-sustainable-form>
            <div class="scfin-demo__two">
              <label><span>Baseline emissions (tCO₂e)</span><input name="baselineEmissions" type="number" min="0" step="100" value="12000"></label>
              <label><span>Project emissions (tCO₂e)</span><input name="projectEmissions" type="number" min="0" step="100" value="7500"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Shadow carbon price</span><input name="carbonPrice" type="number" min="0" step="1" value="85"></label>
              <label><span>Credit price</span><input name="creditPrice" type="number" min="0" step="1" value="42"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Credit quantity</span><input name="creditQuantity" type="number" min="0" step="100" value="4200"></label>
              <label><span>Credit discount (%)</span><input name="creditDiscount" type="number" min="0" max="100" step="1" value="12"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Natural-capital uplift</span><input name="naturalUplift" type="number" step="1000" value="414000"></label>
              <label><span>Annual ecosystem services</span><input name="annualServices" type="number" min="0" step="1000" value="78000"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Green financing principal</span><input name="greenPrincipal" type="number" min="0" step="10000" value="1800000"></label>
              <label><span>Rate savings (%)</span><input name="rateSavings" type="number" min="0" step="0.1" value="1.1"></label>
            </div>
            <label><span>Base project NPV</span><input name="baseNpv" type="number" step="1000" value="125000"></label>
            <div class="scfin-demo__actions">
              <button type="button" data-scfin-sustainable-run>Evaluate sustainable value</button>
              <button type="button" data-scfin-sustainable-download>Download publication</button>
            </div>
          </form>
          <div class="scfin-sustainable__output" aria-live="polite">
            <div class="scfin-demo__metrics">
              <div><span>Avoided emissions</span><strong data-scfin-sustainable-emissions>—</strong></div>
              <div><span>Selected carbon value</span><strong data-scfin-sustainable-carbon>—</strong></div>
              <div><span>Total sustainable value</span><strong data-scfin-sustainable-total>—</strong></div>
              <div><span>Adjusted project NPV</span><strong data-scfin-sustainable-npv>—</strong></div>
            </div>
            <div class="scfin-capital__table-wrap"><table class="scfin-capital__table"><thead><tr><th>Component</th><th>Value</th></tr></thead><tbody data-scfin-sustainable-table></tbody></table></div>
            <ul data-scfin-sustainable-flags></ul>
            <details class="scfin-demo__details"><summary>Versioned sustainable-finance publication</summary><pre data-scfin-sustainable-json></pre></details>
          </div>
        </div>
      </section>

      <section class="scfin-governance" data-scfin-governance-studio>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Evidence and institutional review</p>
          <h3>Governance and publication studio</h3>
          <p>Compile assumptions, sources, evidence, claims, methodology, reviews, approvals, redactions, audit records, and platform handoffs into a reproducible finance brief.</p>
        </div>
        <div class="scfin-sustainable__layout">
          <form class="scfin-sustainable__form" data-scfin-governance-form>
            <label><span>Publication title</span><input name="publicationTitle" type="text" value="Efficiency Retrofit Finance Brief"></label>
            <div class="scfin-demo__two">
              <label><span>Publication state</span><select name="publicationState"><option value="draft">Draft</option><option value="in_review">In review</option><option value="approved">Approved</option><option value="published" selected>Published</option></select></label>
              <label><span>Audience</span><select name="audience"><option value="private">Private</option><option value="internal">Internal</option><option value="public" selected>Public</option></select></label>
            </div>
            <label><span>Brief summary</span><textarea name="publicationSummary" rows="4">A governed finance brief linking headline value claims to assumptions, sources, evidence, methodology, and review history.</textarea></label>
            <div class="scfin-demo__two">
              <label><span>Headline adjusted NPV</span><input name="adjustedNpv" type="number" step="1000" value="1526250.90"></label>
              <label><span>Avoided emissions</span><input name="avoidedEmissions" type="number" step="100" value="4500"></label>
            </div>
            <label><input name="includeObjection" type="checkbox"> Add unresolved reviewer objection</label>
            <div class="scfin-demo__actions">
              <button type="button" data-scfin-governance-run>Compile governed brief</button>
              <button type="button" data-scfin-governance-download>Download publication</button>
              <button type="button" data-scfin-governance-public>Download public view</button>
            </div>
          </form>
          <div class="scfin-sustainable__output" aria-live="polite">
            <div class="scfin-demo__metrics">
              <div><span>Readiness</span><strong data-scfin-governance-status>—</strong></div>
              <div><span>Traced headline claims</span><strong data-scfin-governance-trace>—</strong></div>
              <div><span>Approvals</span><strong data-scfin-governance-approvals>—</strong></div>
              <div><span>Private records excluded</span><strong data-scfin-governance-private>—</strong></div>
            </div>
            <div class="scfin-capital__table-wrap"><table class="scfin-capital__table"><thead><tr><th>Claim</th><th>Metrics</th><th>Sources</th><th>Complete</th></tr></thead><tbody data-scfin-governance-table></tbody></table></div>
            <ul data-scfin-governance-flags></ul>
            <details class="scfin-demo__details"><summary>Decision brief</summary><pre data-scfin-governance-brief></pre></details>
            <details class="scfin-demo__details"><summary>Versioned governance publication</summary><pre data-scfin-governance-json></pre></details>
          </div>
        </div>
      </section>

      <section class="scfin-platform" data-scfin-platform-studio>
        <div class="scfin-capital__header">
          <p class="scfin-demo__eyebrow">Connected institutional finance</p>
          <h3>Financial decision intelligence platform</h3>
          <p>Connect governed finance artifacts to Decision Studio, Knowledge Library, Workbench, and Site Intelligence while preserving classification, provenance, dependency order, and portfolio value.</p>
        </div>
        <div class="scfin-sustainable__layout">
          <form class="scfin-sustainable__form" data-scfin-platform-form>
            <div class="scfin-demo__two">
              <label><span>Retrofit adjusted NPV</span><input name="retrofitNpv" type="number" step="1000" value="1526250.9"></label>
              <label><span>Pricing adjusted NPV</span><input name="pricingNpv" type="number" step="1000" value="260000"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Retrofit confidence (%)</span><input name="retrofitConfidence" type="number" min="0" max="100" value="85"></label>
              <label><span>Pricing confidence (%)</span><input name="pricingConfidence" type="number" min="0" max="100" value="82"></label>
            </div>
            <div class="scfin-demo__two">
              <label><span>Site Intelligence status</span><select name="intelligenceStatus"><option value="online">Online</option><option value="degraded" selected>Degraded</option><option value="offline">Offline</option></select></label>
              <label><span>Minimum case confidence (%)</span><input name="minimumConfidence" type="number" min="0" max="100" value="70"></label>
            </div>
            <label><input name="includeRejectedHandoff" type="checkbox" checked> Include rejected confidential Knowledge Library handoff</label>
            <div class="scfin-demo__actions">
              <button type="button" data-scfin-platform-run>Evaluate connected portfolio</button>
              <button type="button" data-scfin-platform-download>Download platform publication</button>
            </div>
          </form>
          <div class="scfin-sustainable__output" aria-live="polite">
            <div class="scfin-demo__metrics">
              <div><span>Adjusted portfolio NPV</span><strong data-scfin-platform-npv>—</strong></div>
              <div><span>Risk-adjusted value</span><strong data-scfin-platform-risk>—</strong></div>
              <div><span>Decision-ready cases</span><strong data-scfin-platform-cases>—</strong></div>
              <div><span>Completed handoffs</span><strong data-scfin-platform-handoffs>—</strong></div>
            </div>
            <div class="scfin-capital__table-wrap"><table class="scfin-capital__table"><thead><tr><th>Decision case</th><th>Status</th><th>Readiness</th><th>Risk-adjusted value</th></tr></thead><tbody data-scfin-platform-table></tbody></table></div>
            <ul data-scfin-platform-flags></ul>
            <details class="scfin-demo__details"><summary>Integration manifest</summary><pre data-scfin-platform-manifest></pre></details>
            <details class="scfin-demo__details"><summary>Versioned platform publication</summary><pre data-scfin-platform-json></pre></details>
          </div>
        </div>
      </section>
      <p class="scfin-demo__disclaimer">Educational scenario tool only. Not financial, investment, tax, accounting, legal, assurance, or fiduciary advice. Browser workspace data remains in this browser until exported or deleted.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('catalyst_finance_demo', 'catalyst_finance_demo_shortcode');
add_shortcode('catalyst_finance_workspace', 'catalyst_finance_demo_shortcode');
