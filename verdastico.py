import streamlit as st
import streamlit.components.v1 as components


def main():
    components.html("""
     <canvas id="fireworksCanvas"></canvas>

    <script>
  var canvas = document.getElementById('fireworksCanvas');
    var ctx = canvas.getContext('2d');

    // Set the canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    var bgImage = new Image();
    bgImage.src = 'https://s3.us-east-2.amazonaws.com/observer1.0/images.jpg'; // Replace with the URL of your image

    bgImage.onload = function() {
        console.log("Image loaded");
        ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);
        draw(); // Start the fireworks animation after the image has loaded
    };

    bgImage.onerror = function() {
        console.error("Error loading the image.");
    };
// Function to create a random color
function randomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Function to create a single particle
function Particle(x, y) {
    this.x = x;
    this.y = y;
    this.radius = Math.random() * 5 + 1;
    this.color = randomColor();
    this.lifeSpan = Math.random() * 50 + 80;
    this.vx = Math.random() * 2 - 1;
    this.vy = Math.random() * 2 - 1;

    this.draw = function() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, 2 * Math.PI);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
}

// Array to hold particles
var particles = [];

// Function to create a group of particles (a single firework)
function createFirework() {
    var x = Math.random() * canvas.width;
    var y = Math.random() * canvas.height;

    for (var i = 0; i < 100; i++) {
        particles.push(new Particle(x, y));
    }
}

// Animation loop
 function draw() {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw background image
        ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);

        // Draw particles (fireworks)
        particles.forEach(function(particle, index) {
            particle.lifeSpan--;
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.draw();

            // Remove particles that are dead (lifeSpan <= 0)
            if (particle.lifeSpan <= 0) {
                particles.splice(index, 1);
            }
        });

        // Generate a new firework periodically
        if (Math.random() < 0.02) {
            createFirework();
        }

        requestAnimationFrame(draw);
    }

// Start the animation
draw();

</script>


""", height=1000)


if __name__ == "__main__":
    main()
