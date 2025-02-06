package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/farmergreg/rfsnotify"
	"gopkg.in/fsnotify.v1"
)

type Config struct {
	IgnoredPatterns []string `json:"ignored_patterns"`
	LastChange      *Change  `json:"last_change,omitempty"`
	BlenderPath     string   `json:"blender_path"`
	WatchedDirs     []string `json:"watched_dirs"`
}

type Change struct {
	Path    string    `json:"path"`
	ModTime time.Time `json:"mod_time"`
}

func readConfig() (*Config, error) {
	configFile := ".hotreload"
	if _, err := os.Stat(configFile); os.IsNotExist(err) {
		return &Config{}, fmt.Errorf("no .hotreload found in current directory")
	}

	data, err := os.ReadFile(configFile)
	if err != nil {
		return nil, err
	}

	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, err
	}

	return &config, nil
}

func writeConfig(config *Config) error {
	oldConfig, oldErr := readConfig()
	if oldErr != nil {
		return oldErr
	}
	oldConfig.LastChange = config.LastChange
	data, err := json.MarshalIndent(oldConfig, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(".hotreload", data, 0644)
}

func shouldIgnore(file string, ignoredPatterns []string) bool {
	for _, pattern := range ignoredPatterns {
		matched, _ := filepath.Match(pattern, file)
		if matched {
			return true
		}
	}
	return false
}

var blenderCmd *exec.Cmd

func runBlender(config *Config) {
	if blenderCmd == nil || blenderCmd.ProcessState != nil {
		if config.BlenderPath == "" {
			log.Println("Blender path not set in config")
			return
		}

		blenderCmd = exec.Command(config.BlenderPath)
		blenderCmd.Stdout = os.Stdout
		blenderCmd.Stderr = os.Stderr

		env := os.Environ()
		cwd, err := os.Getwd()
		if err != nil {
			fmt.Printf("Error getting current working directory: %v", err)
			return
		}
		env = append(env, fmt.Sprintf("HOTRELOAD_WATCHED_DIR=%s", cwd))
		blenderCmd.Env = env

		if err := blenderCmd.Start(); err != nil {
			log.Printf("Error starting Blender: %v", err)
			return
		}

		go func() {
			if err := blenderCmd.Wait(); err != nil {
				log.Printf("Blender exited with error: %v", err)
			}
		}()

		fmt.Println("Blender started in background")
	} else {
		fmt.Println("Blender is already running")
	}
}

func onChange(event fsnotify.Event, config *Config) {
	fmt.Printf("File changed: %s\n", event.Name)
	info, err := os.Stat(event.Name)
	if err != nil {
		log.Printf("Error getting file info: %v", err)
		return
	}
	runBlender(config)

	config.LastChange = &Change{
		Path:    event.Name,
		ModTime: info.ModTime(),
	}

	if err := writeConfig(config); err != nil {
		log.Printf("Error writing config: %v", err)
	}
}

var (
	debounceDelay = 1 * time.Second
	debounceTimer *time.Timer
)

func main() {
	config, err := readConfig()
	if err != nil {
		log.Fatalf("Error reading config: %v", err)
	}

	log.Printf("Loaded config: %+v", config)

	watcher, err := rfsnotify.NewWatcher()
	if err != nil {
		log.Fatalf("Error creating watcher: %v", err)
	}
	defer watcher.Close()

	err = watcher.AddRecursive(".")
	if err != nil {
		log.Fatalf("Error adding watcher: %v", err)
	}

	cwd, err := os.Getwd()
	if err != nil {
		log.Fatalf("Error getting current working directory: %v", err)
	}
	log.Printf("Watching for changes in %s", cwd)

	runBlender(config)

	done := make(chan bool)
	go func() {
		for {
			select {
			case event, ok := <-watcher.Events:
				if !ok {
					return
				}
				if event.Op&fsnotify.Write == fsnotify.Write {
					if strings.HasPrefix(event.Name, ".idea") || strings.HasPrefix(event.Name, ".hotreload") || strings.HasSuffix(event.Name, "~") {
						continue
					}
					if strings.Contains(event.Name, "__pycache__") {
						continue
					}
					if shouldIgnore(event.Name, config.IgnoredPatterns) {
						continue
					}
					if debounceTimer != nil {
						debounceTimer.Stop()
					}
					debounceTimer = time.AfterFunc(debounceDelay, func() {
						onChange(event, config)
					})
				}
			case err, ok := <-watcher.Errors:
				if !ok {
					return
				}
				log.Printf("Watcher error: %v", err)
			}
		}
	}()

	<-done
}
