<?php
/**
 * Plugin Name: Catalyst Finance Demo
 * Description: Browser-based Catalyst Finance scenario demo for Sustainable Catalyst.
 * Version: 1.0.1
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

define('CATALYST_FINANCE_DEMO_VERSION', '1.0.1');

function catalyst_finance_demo_assets() {
    $base = plugin_dir_url(__FILE__);
    $path = plugin_dir_path(__FILE__);
    wp_enqueue_style(
        'catalyst-finance-demo',
        $base . 'assets/catalyst-finance-demo.css',
        array(),
        CATALYST_FINANCE_DEMO_VERSION
    );
    wp_enqueue_script(
        'catalyst-finance-demo',
        $base . 'assets/catalyst-finance-demo.js',
        array(),
        CATALYST_FINANCE_DEMO_VERSION,
        true
    );
}

function catalyst_finance_demo_shortcode($atts = array()) {
    catalyst_finance_demo_assets();
    ob_start();
    ?>
    <section class="scfin-demo" data-scfin-demo>
      <div class="scfin-demo__header">
        <p class="scfin-demo__eyebrow">Interactive Finance Scenario</p>
        <h3>Build a reviewable finance case</h3>
        <p>Estimate net annual benefit, payback, NPV, ROI, benefit-cost ratio, carbon cost per ton, and a risk-adjusted review score.</p>
      </div>

      <div class="scfin-demo__grid">
        <form class="scfin-demo__form" data-scfin-form>
          <label>
            <span>Initiative</span>
            <input name="projectName" type="text" value="Building efficiency retrofit">
          </label>

          <label>
            <span>Category</span>
            <input name="category" type="text" value="Energy efficiency">
          </label>

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
              <input name="timeHorizon" type="number" min="1" max="40" step="1" value="10">
            </label>
            <label>
              <span>Discount rate (%)</span>
              <input name="discountRate" type="number" min="0" max="30" step="0.1" value="6">
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

          <div class="scfin-demo__actions">
            <button type="button" data-scfin-copy>Copy JSON</button>
            <button type="button" data-scfin-download>Download JSON</button>
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
            <summary>JSON export</summary>
            <pre data-scfin-json></pre>
          </details>
        </div>
      </div>

      <p class="scfin-demo__disclaimer">Educational scenario tool only. Not financial, investment, tax, accounting, legal, assurance, or fiduciary advice.</p>
    </section>
    <?php
    return ob_get_clean();
}
add_shortcode('catalyst_finance_demo', 'catalyst_finance_demo_shortcode');
