function createFlower() {
    let flower = document.createElement("div");
    flower.classList.add("flower");
    flower.innerHTML = "🍇";
    flower.style.left = Math.random() * window.innerWidth + "px";
    flower.style.animationDuration = (Math.random() * 3 + 2) + "s";
    document.body.appendChild(flower);
    setTimeout(() => flower.remove(), 5000);
}
setInterval(createFlower, 200);
console.log("Script loaded");
