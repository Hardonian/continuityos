// Package continuityos provides the official Go Client SDK for ContinuityOS.
package continuityos

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Client represents a ContinuityOS API client.
type Client struct {
	BaseURL    string
	APIKey     string
	HTTPClient *http.Client
}

// CorridorStatus represents operational state of a corridor.
type CorridorStatus struct {
	CorridorID     string    `json:"corridor_id"`
	EffectiveState string    `json:"effective_state"`
	ResilienceScore float64  `json:"resilience_score"`
	ClosureReason  string    `json:"closure_reason"`
	ReconciledAt   time.Time `json:"reconciled_at"`
}

// NewClient initializes a new ContinuityOS Go client.
func NewClient(baseURL, apiKey string) *Client {
	if baseURL == "" {
		baseURL = "http://127.0.0.1:8082"
	}
	return &Client{
		BaseURL: baseURL,
		APIKey:  apiKey,
		HTTPClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// GetCorridorStatus fetches the real-time operational status of a corridor.
func (c *Client) GetCorridorStatus(corridorID string) (*CorridorStatus, error) {
	reqURL := fmt.Sprintf("%s/v1/corridors/%s/status", c.BaseURL, corridorID)
	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, err
	}
	if c.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+c.APIKey)
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("continuityos: api error: status %d", resp.StatusCode)
	}

	var status CorridorStatus
	if err := json.NewDecoder(resp.Body).Decode(&status); err != nil {
		return nil, err
	}
	return &status, nil
}
