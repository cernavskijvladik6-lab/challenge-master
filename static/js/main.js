// Main JavaScript for Challenge Master

// Check if user is logged in
async function checkAuth() {
    try {
        const response = await fetch('/api/user');
        if (response.ok) {
            const user = await response.json();
            updateUserUI(user);
            return user;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

// Update UI with user data
function updateUserUI(user) {
    // Show user menu
    const userMenu = document.getElementById('user-menu');
    const loginMenu = document.getElementById('login-menu');
    const adminMenu = document.getElementById('admin-menu');
    
    if (userMenu) userMenu.style.display = 'block';
    if (loginMenu) loginMenu.style.display = 'none';
    
    if (user.is_admin && adminMenu) {
        adminMenu.style.display = 'block';
    }
    
    // Show user stats
    const userStats = document.getElementById('user-stats');
    if (userStats) {
        userStats.style.display = 'flex';
        document.getElementById('coins').textContent = user.coins;
        document.getElementById('crystals').textContent = user.crystals;
        document.getElementById('power_points').textContent = user.power_points;
    }
}

// Change language
async function changeLanguage(lang) {
    await fetch(`/api/user/language/${lang}`, { method: 'POST' });
    location.reload();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', checkAuth);

// Utility functions for games
const GameUtils = {
    saveScore: function(gameName, score) {
        const scores = JSON.parse(localStorage.getItem('game_scores') || '{}');
        if (!scores[gameName] || scores[gameName] < score) {
            scores[gameName] = score;
            localStorage.setItem('game_scores', JSON.stringify(scores));
        }
        return scores[gameName];
    },
    
    getScore: function(gameName) {
        const scores = JSON.parse(localStorage.getItem('game_scores') || '{}');
        return scores[gameName] || 0;
    },
    
    addCoins: function(amount) {
        const coins = parseInt(document.getElementById('coins').textContent || 0);
        document.getElementById('coins').textContent = coins + amount;
    },
    
    addExperience: function(amount) {
        console.log('Added ' + amount + ' experience');
    }
};

// Snake Game
const SnakeGame = {
    canvas: null,
    ctx: null,
    gridSize: 20,
    snake: [{x: 10, y: 10}],
    food: {x: 15, y: 15},
    direction: {x: 1, y: 0},
    nextDirection: {x: 1, y: 0},
    score: 0,
    gameRunning: false,
    gameSpeed: 100,
    
    init: function(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = 400;
        this.canvas.height = 400;
        this.gameRunning = true;
        this.score = 0;
        
        this.setupControls();
        this.gameLoop();
    },
    
    setupControls: function() {
        const self = this;
        document.addEventListener('keydown', (e) => {
            switch(e.key.toLowerCase()) {
                case 'arrowup': case 'w':
                    if (this.direction.y === 0) this.nextDirection = {x: 0, y: -1};
                    break;
                case 'arrowdown': case 's':
                    if (this.direction.y === 0) this.nextDirection = {x: 0, y: 1};
                    break;
                case 'arrowleft': case 'a':
                    if (this.direction.x === 0) this.nextDirection = {x: -1, y: 0};
                    break;
                case 'arrowright': case 'd':
                    if (this.direction.x === 0) this.nextDirection = {x: 1, y: 0};
                    break;
            }
        });
    },
    
    gameLoop: function() {
        if (!this.gameRunning) return;
        
        this.update();
        this.draw();
        
        setTimeout(() => this.gameLoop(), this.gameSpeed);
    },
    
    update: function() {
        this.direction = this.nextDirection;
        
        const head = {
            x: this.snake[0].x + this.direction.x,
            y: this.snake[0].y + this.direction.y
        };
        
        // Check collisions with wall
        if (head.x < 0 || head.x >= 20 || head.y < 0 || head.y >= 20) {
            this.gameRunning = false;
            this.endGame();
            return;
        }
        
        // Check collision with self
        if (this.snake.some(segment => segment.x === head.x && segment.y === head.y)) {
            this.gameRunning = false;
            this.endGame();
            return;
        }
        
        this.snake.unshift(head);
        
        // Check if food eaten
        if (head.x === this.food.x && head.y === this.food.y) {
            this.score += 10;
            this.spawnFood();
        } else {
            this.snake.pop();
        }
    },
    
    draw: function() {
        this.ctx.fillStyle = '#0a0e27';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw snake
        this.ctx.fillStyle = '#00d9ff';
        this.snake.forEach((segment, index) => {
            const x = segment.x * this.gridSize;
            const y = segment.y * this.gridSize;
            this.ctx.fillRect(x + 1, y + 1, this.gridSize - 2, this.gridSize - 2);
            
            if (index === 0) {
                this.ctx.fillStyle = '#00a8cc';
                this.ctx.fillRect(x + 3, y + 3, this.gridSize - 6, this.gridSize - 6);
                this.ctx.fillStyle = '#00d9ff';
            }
        });
        
        // Draw food
        this.ctx.fillStyle = '#ff6b6b';
        const foodX = this.food.x * this.gridSize;
        const foodY = this.food.y * this.gridSize;
        this.ctx.beginPath();
        this.ctx.arc(foodX + this.gridSize/2, foodY + this.gridSize/2, this.gridSize/2 - 2, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Draw score
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = '16px Arial';
        this.ctx.fillText('Score: ' + this.score, 10, 20);
    },
    
    spawnFood: function() {
        this.food = {
            x: Math.floor(Math.random() * 20),
            y: Math.floor(Math.random() * 20)
        };
    },
    
    endGame: function() {
        alert('Game Over! Score: ' + this.score);
        const bestScore = GameUtils.saveScore('snake', this.score);
        GameUtils.addCoins(Math.floor(this.score / 10));
        console.log('Best score:', bestScore);
    }
};

// Shooter Game
const ShooterGame = {
    canvas: null,
    ctx: null,
    player: {x: 50, y: 300, width: 40, height: 40, speed: 5},
    enemies: [],
    bullets: [],
    score: 0,
    gameRunning: false,
    
    init: function(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = 400;
        this.canvas.height = 400;
        this.gameRunning = true;
        this.score = 0;
        
        this.setupControls();
        this.spawnEnemies();
        this.gameLoop();
    },
    
    setupControls: function() {
        document.addEventListener('keydown', (e) => {
            if (e.key === ' ') {
                e.preventDefault();
                this.shoot();
            }
            if (e.key === 'ArrowUp') this.player.y = Math.max(0, this.player.y - this.player.speed);
            if (e.key === 'ArrowDown') this.player.y = Math.min(360, this.player.y + this.player.speed);
            if (e.key === 'ArrowLeft') this.player.x = Math.max(0, this.player.x - this.player.speed);
            if (e.key === 'ArrowRight') this.player.x = Math.min(360, this.player.x + this.player.speed);
        });
    },
    
    shoot: function() {
        this.bullets.push({
            x: this.player.x + 40,
            y: this.player.y + 20,
            width: 10,
            height: 5,
            speed: 7
        });
    },
    
    spawnEnemies: function() {
        for (let i = 0; i < 3; i++) {
            this.enemies.push({
                x: 350,
                y: Math.random() * 360,
                width: 30,
                height: 30,
                speed: 2
            });
        }
    },
    
    gameLoop: function() {
        if (!this.gameRunning) return;
        
        this.update();
        this.draw();
        
        requestAnimationFrame(() => this.gameLoop());
    },
    
    update: function() {
        // Update bullets
        this.bullets = this.bullets.filter(bullet => {
            bullet.x += bullet.speed;
            
            for (let i = 0; i < this.enemies.length; i++) {
                const enemy = this.enemies[i];
                if (this.checkCollision(bullet, enemy)) {
                    this.enemies.splice(i, 1);
                    this.score += 10;
                    return false;
                }
            }
            
            return bullet.x < this.canvas.width;
        });
        
        // Update enemies
        this.enemies.forEach(enemy => {
            enemy.x -= enemy.speed;
            
            if (this.checkCollision(this.player, enemy)) {
                this.gameRunning = false;
                this.endGame();
            }
        });
        
        if (this.enemies.length === 0 && Math.random() < 0.02) {
            this.spawnEnemies();
        }
    },
    
    draw: function() {
        this.ctx.fillStyle = '#0a0e27';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw player
        this.ctx.fillStyle = '#00d9ff';
        this.ctx.fillRect(this.player.x, this.player.y, this.player.width, this.player.height);
        
        // Draw bullets
        this.ctx.fillStyle = '#ffff00';
        this.bullets.forEach(bullet => {
            this.ctx.fillRect(bullet.x, bullet.y, bullet.width, bullet.height);
        });
        
        // Draw enemies
        this.ctx.fillStyle = '#ff6b6b';
        this.enemies.forEach(enemy => {
            this.ctx.fillRect(enemy.x, enemy.y, enemy.width, enemy.height);
        });
        
        // Draw score
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = '16px Arial';
        this.ctx.fillText('Score: ' + this.score, 10, 20);
    },
    
    checkCollision: function(obj1, obj2) {
        return obj1.x < obj2.x + obj2.width &&
               obj1.x + obj1.width > obj2.x &&
               obj1.y < obj2.y + obj2.height &&
               obj1.y + obj1.height > obj2.y;
    },
    
    endGame: function() {
        alert('Game Over! Score: ' + this.score);
        const bestScore = GameUtils.saveScore('shooter', this.score);
        GameUtils.addCoins(Math.floor(this.score / 10));
    }
};

console.log('Main.js loaded successfully');
