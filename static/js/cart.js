/* ═══════════════════════════════════════
   MPOMBO UNIVERSAL CART
   Works on homepage, menu, order pages
═══════════════════════════════════════ */
(function(){
  const ugx = n => 'UGX ' + Math.round(n).toLocaleString();
  const CART_KEY = 'mpombo_cart';

  function getCart(){ return JSON.parse(sessionStorage.getItem(CART_KEY)||'[]'); }
  function saveCart(c){ sessionStorage.setItem(CART_KEY, JSON.stringify(c)); }

  function cartCount(){ return getCart().reduce((s,i)=>s+i.qty,0); }
  function cartTotal(){ return getCart().reduce((s,i)=>s+i.price*i.qty,0); }

  /* ── Inject floating cart button (bottom-left) ── */
  function injectCartButton(){
    if(document.getElementById('uCart')) return;
    const btn = document.createElement('div');
    btn.id = 'uCart';
    btn.innerHTML = `
      <div id="uCartInner">
        <i class="fas fa-shopping-bag"></i>
        <div id="uCartInfo" style="display:none">
          <span id="uCartCnt"></span>
          <span id="uCartTot"></span>
        </div>
        <span id="uCartBadge" style="display:none"></span>
      </div>
    `;
    btn.onclick = () => {
      const isOrderPage = window.location.pathname === '/order';
      if(isOrderPage){
        const panel = document.getElementById('cartDrawer');
        if(panel) panel.classList.toggle('open');
      } else {
        window.location.href = '/order';
      }
    };
    document.body.appendChild(btn);

    const style = document.createElement('style');
    style.textContent = `
      #uCart{
        position:fixed;bottom:92px;left:20px;z-index:996;
        background:var(--forest);border-radius:50px;
        padding:11px 16px;cursor:pointer;
        box-shadow:0 6px 24px rgba(0,0,0,.25);
        transition:all .3s;display:none;
        align-items:center;gap:10px;
      }
      #uCart:hover{background:var(--forest2);transform:translateY(-2px)}
      #uCart.visible{display:flex}
      #uCartInner{display:flex;align-items:center;gap:9px}
      #uCartInner i{color:var(--gold2);font-size:18px;flex-shrink:0}
      #uCartInfo{flex-direction:column;gap:1px}
      #uCartInfo span:first-child{font-size:11px;color:rgba(255,255,255,.65);display:block}
      #uCartInfo span:last-child{font-family:'Yeseva One',serif;font-size:16px;color:var(--gold2);display:block}
      #uCartBadge{
        background:var(--clay);color:white;border-radius:50%;
        width:20px;height:20px;font-size:10px;font-weight:700;
        display:flex;align-items:center;justify-content:center;
        flex-shrink:0;
      }
    `;
    document.head.appendChild(style);
  }

  function updateCartButton(){
    const btn = document.getElementById('uCart');
    if(!btn) return;
    const cnt = cartCount();
    const tot = cartTotal();
    btn.classList.toggle('visible', cnt > 0);
    const info = document.getElementById('uCartInfo');
    const badge = document.getElementById('uCartBadge');
    if(info){
      info.style.display = cnt > 0 ? 'flex' : 'none';
      document.getElementById('uCartCnt').textContent = cnt + (cnt===1?' item':' items');
      document.getElementById('uCartTot').textContent = ugx(tot);
    }
    if(badge){
      badge.style.display = cnt > 0 ? 'flex' : 'none';
      badge.textContent = cnt > 9 ? '9+' : cnt;
    }
  }

  /* ── Public API ── */
  window.MCart = {
    get: getCart,
    save: saveCart,
    add(id, name, price, qty=1){
      const cart = getCart();
      const ex = cart.find(i=>i.id===id);
      if(ex){ ex.qty += qty; if(ex.qty<=0) return this.remove(id); }
      else cart.push({id,name,price,qty});
      saveCart(cart);
      updateCartButton();
      return getCart();
    },
    remove(id){
      saveCart(getCart().filter(i=>i.id!==id));
      updateCartButton();
    },
    clear(){ saveCart([]); updateCartButton(); },
    count: cartCount,
    total: cartTotal,
    update: updateCartButton,
  };

  // Init on DOM ready
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', ()=>{ injectCartButton(); updateCartButton(); });
  } else {
    injectCartButton(); updateCartButton();
  }
})();
