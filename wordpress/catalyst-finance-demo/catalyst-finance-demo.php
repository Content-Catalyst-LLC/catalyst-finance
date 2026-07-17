<?php
/**
 * Plugin Name: Catalyst Finance Demo
 * Description: Persistent browser-based Catalyst Finance scenario workspace for Sustainable Catalyst.
 * Version: 1.2.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

define('CATALYST_FINANCE_DEMO_VERSION', '1.2.0');

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
        'catalyst-finance-demo',
        $base . 'assets/catalyst-finance-demo.js',
        array('catalyst-finance-engine'),
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
        <p class="scfin-demo__eyebrow">Catalyst Finance v1.2.0</p>
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

      <p class="scfin-demo__disclaimer">Educational scenario tool only. Not financial, investment, tax, accounting, legal, assurance, or fiduciary advice. Browser workspace data remains in this browser until exported or deleted.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('catalyst_finance_demo', 'catalyst_finance_demo_shortcode');
add_shortcode('catalyst_finance_workspace', 'catalyst_finance_demo_shortcode');
