(() => {
 function go(id){if(id==='F'||id==='L')location.replace('/due-camere/?variante='+id);}
 go(new URLSearchParams(location.search).get('variante'));
 document.addEventListener('change',e=>{if(e.target.id==='version'&&['F','L'].includes(e.target.value)){e.stopImmediatePropagation();go(e.target.value);}},true);
})();