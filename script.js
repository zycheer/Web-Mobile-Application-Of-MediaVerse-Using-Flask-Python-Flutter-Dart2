// Function to open a specific tab and show its content, hiding others
function openTab(tabId) {
  // Hide all content sections
  const sections = document.querySelectorAll('.content-section');
  sections.forEach(section => {
    section.style.display = 'none'; // Hide all sections
    section.classList.remove('active'); // Remove active class
  });

  // Remove 'active' class from all sidebar links
  const sidebarLinks = document.querySelectorAll('.sidebar a');
  sidebarLinks.forEach(link => {
    link.classList.remove('active'); // Remove active state
  });

  // Show the selected section
  const activeSection = document.getElementById(tabId);
  if (activeSection) {
    activeSection.style.display = 'block'; // Show the selected section
    activeSection.classList.add('active'); // Add active class to it
  }

  // Add 'active' class to the clicked sidebar link
  const activeLink = document.querySelector(`.sidebar a[onclick="openTab('${tabId}')"]`);
  if (activeLink) {
    activeLink.classList.add('active'); // Highlight the selected tab
  }
}

// Initialize the default tab on page load (e.g., 'dashboard' or 'inventory')
document.addEventListener('DOMContentLoaded', () => {
  openTab('dashboard'); // Set 'dashboard' as the default tab, or use another default tab
});


// Function to filter users in the Customers section
function filterUsers() {
  const input = document.getElementById('search-input');
  const filter = input.value.toLowerCase();
  const table = document.getElementById('user-grid');
  const tr = table.getElementsByTagName('tr');

  for (let i = 1; i < tr.length; i++) { // Start from 1 to skip header row
    const td = tr[i].getElementsByTagName('td');
    let txtValue = '';
    for (let j = 0; j < td.length - 1; j++) { // Exclude the last column (Last Login)
      if (td[j]) {
        txtValue += td[j].textContent || td[j].innerText;
      }
    }
    if (txtValue.toLowerCase().indexOf(filter) > -1) {
      tr[i].style.display = '';
    } else {
      tr[i].style.display = 'none';
    }
  }
}

// Function to sort table columns
function sortTable(n) {
  const table = document.getElementById("user-grid");
  let switching = true;
  let dir = "asc"; 
  let switchcount = 0;

  while (switching) {
    switching = false;
    const rows = table.rows;
    for (let i = 1; i < (rows.length - 1); i++) {
      let shouldSwitch = false;
      const x = rows[i].getElementsByTagName("TD")[n];
      const y = rows[i + 1].getElementsByTagName("TD")[n];
      let cmpX = x.textContent || x.innerText;
      let cmpY = y.textContent || y.innerText;

      // Convert to numbers if possible
      if (!isNaN(parseFloat(cmpX)) && !isNaN(parseFloat(cmpY))) {
        cmpX = parseFloat(cmpX);
        cmpY = parseFloat(cmpY);
      }

      if (dir === "asc") {
        if (cmpX > cmpY) {
          shouldSwitch = true;
          break;
        }
      } else if (dir === "desc") {
        if (cmpX < cmpY) {
          shouldSwitch = true;
          break;
        }
      }
    }

    if (shouldSwitch) {
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      switchcount++;      
    } else {
      if (switchcount === 0 && dir === "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}




// Dark Mode Toggle
const themeToggler = document.querySelector('.theme-toggler');
const rootElement = document.documentElement;

themeToggler.addEventListener('click', () => {
    rootElement.classList.toggle('dark-theme-variables');
    
    // Toggle active class on the theme toggler
    themeToggler.querySelector('span:nth-child(1)').classList.toggle('active');
    themeToggler.querySelector('span:nth-child(2)').classList.toggle('active');
});

  // Toggle the Product dropdown
  function toggleProductDropdown() {
    const dropdown = document.getElementById("product-dropdown");
    
    // Toggle between showing and hiding the dropdown
    if (dropdown.style.display === "none" || dropdown.style.display === "") {
      dropdown.style.display = "block"; // Show the dropdown
    } else {
      dropdown.style.display = "none"; // Hide the dropdown
    }
  }
  
// Function to toggle the product dropdown and activate the button
function toggleProductDropdown() {
  // First, remove the "active" class from all sidebar links
  const sidebarLinks = document.querySelectorAll('.sidebar a');
  sidebarLinks.forEach(link => link.classList.remove('active'));

  // Now, add the "active" class to the "Product" button
  const productButton = document.querySelector('a[onclick="toggleProductDropdown()"]');
  productButton.classList.add('active');

  // Toggle the Product dropdown visibility
  const dropdown = document.getElementById("product-dropdown");
  if (dropdown.style.display === "none" || dropdown.style.display === "") {
    dropdown.style.display = "block"; // Show the dropdown
  } else {
    dropdown.style.display = "none"; // Hide the dropdown
  }
}

// Function to toggle the product dropdown and activate the button
function toggleProductDropdown() {
  // First, remove the "active" class from all sidebar links
  const sidebarLinks = document.querySelectorAll('.sidebar a');
  sidebarLinks.forEach(link => link.classList.remove('active'));

  // Add the "active" class to the "Product" button
  const productButton = document.querySelector('a[onclick="toggleProductDropdown()"]');
  productButton.classList.add('active');

  // Toggle the Product dropdown visibility
  const dropdown = document.getElementById("product-dropdown");
  dropdown.style.display = (dropdown.style.display === "none" || dropdown.style.display === "") ? "block" : "none";
}

// Function to open the product's dropdown links and manage the active state
function openProductTab(tabId) {
  // Remove the active class from both "Add Product" and "Inventory"
  const dropdownLinks = document.querySelectorAll('#product-dropdown li');
  dropdownLinks.forEach(link => link.classList.remove('active'));

  // Add the active class to the clicked dropdown item
  const activeDropdownLink = document.getElementById(tabId);
  activeDropdownLink.classList.add('active');

  // Hide all content sections
  const sections = document.querySelectorAll('.content-section');
  sections.forEach(section => section.style.display = 'none');

  // Show the selected tab's section
  document.getElementById(tabId).style.display = 'block';
}

// Function to open other tabs (like "Dashboard") and manage active state
function openTab(tabId) {
  // Remove the "active" class from all links first
  const sidebarLinks = document.querySelectorAll('.sidebar a');
  sidebarLinks.forEach(link => link.classList.remove('active'));

  // Remove the "active" class from product dropdown items too
  const dropdownLinks = document.querySelectorAll('#product-dropdown li');
  dropdownLinks.forEach(link => link.classList.remove('active'));

  // Add "active" class to the clicked button
  const activeButton = document.querySelector(`a[onclick="openTab('${tabId}')"]`);
  if (activeButton) activeButton.classList.add('active');

  // Hide all content sections
  const sections = document.querySelectorAll('.content-section');
  sections.forEach(section => section.style.display = 'none');

  // Show the selected tab's section
  document.getElementById(tabId).style.display = 'block';
}
// Function to show the inventory section
function showInventory() {
  const sections = document.querySelectorAll('.content-section');
  sections.forEach(section => section.style.display = 'none');
  document.getElementById('inventory').style.display = 'block';
  displayInventory();
}
document.getElementById('addProductForm').addEventListener('submit', function(event) {
  event.preventDefault(); // Prevent default form submission

  // Get form values
  const productName = document.getElementById('product_name').value;
  const productPrice = document.getElementById('price').value;
  const productCategory = document.getElementById('category').value;
  const productDescription = document.getElementById('description').value;

  // Create product object
  const product = {
    name: productName,
    price: productPrice,
    category: productCategory,
    description: productDescription
  };

  // Save to local storage (simulating database)
  let products = JSON.parse(localStorage.getItem('products')) || [];
  products.push(product);
  localStorage.setItem('products', JSON.stringify(products));

  // Clear the form
  this.reset();

  // Show inventory
  showInventory();
});

// Function to display inventory
function displayInventory() {
  const inventoryTableBody = document.getElementById('inventoryTableBody');
  inventoryTableBody.innerHTML = ''; // Clear existing content

  // Retrieve products from local storage
  let products = JSON.parse(localStorage.getItem('products')) || [];

  // Populate the inventory table
  products.forEach(product => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${product.name}</td>
      <td>${product.price}</td>
      <td>${product.category}</td>
      <td>${product.description}</td>
    `;
    inventoryTableBody.appendChild(row);
  });
}

function confirmLogout(event) {
  // Prevent the default action of the link
  event.preventDefault();

  // Show confirmation dialog
  const confirmed = confirm("Are you sure you want to log out?");

  // If user confirms, redirect to the logout route
  if (confirmed) {
    window.location.href = "/logout";
  }
}
    function filterProducts(tab) {
        // Get references to the product sections
        const listedProducts = document.getElementById('listed-products');
        const unlistedProducts = document.getElementById('unlisted-products');

        // Get references to the buttons
        const listedTab = document.getElementById('listed-tab');
        const unlistedTab = document.getElementById('unlisted-tab');

        // Toggle visibility based on the selected tab
        if (tab === 'listed') {
            listedProducts.style.display = 'block';
            unlistedProducts.style.display = 'none';
            listedTab.classList.add('active');
            unlistedTab.classList.remove('active');
        } else if (tab === 'unlisted') {
            listedProducts.style.display = 'none';
            unlistedProducts.style.display = 'block';
            listedTab.classList.remove('active');
            unlistedTab.classList.add('active');
        }
    }

    // Set the default view to 'Listed' on page load
    document.addEventListener('DOMContentLoaded', () => {
        filterProducts('listed');
    });
// Sorting function
function sortTable(columnIndex) {
  const table = document.getElementById('order-grid');
  const rows = Array.from(table.rows).slice(1); // Skip the header row
  const isAscending = table.dataset.sortOrder === 'asc';
  table.dataset.sortOrder = isAscending ? 'desc' : 'asc';

  rows.sort((a, b) => {
      const aText = a.cells[columnIndex].textContent.trim();
      const bText = b.cells[columnIndex].textContent.trim();
      return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
  });

  // Reorder rows in the table
  const tbody = table.querySelector('tbody');
  rows.forEach(row => tbody.appendChild(row));
}

// Filter function
function filterOrders() {
  const input = document.getElementById('search-input').value.toLowerCase();
  const rows = document.querySelectorAll('#order-grid tbody tr');

  rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(input) ? '' : 'none';
  });
}

